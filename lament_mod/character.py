import random
import math
import numpy as np
import lament_mod.tools as tools

from enum import Enum


class CharClass(Enum):
    CLERIC = "Cleric".casefold()
    FIGHTER = "Fighter".casefold()
    MAGIC_USER = "Magic-User".casefold()
    SPECIALIST = "Specialist".casefold()
    DWARF = "Dwarf".casefold()
    ELF = "Elf".casefold()
    HALFLING = "Halfling".casefold()


# This map will allow us to use the string value we get from the API to assign an Enum.
CLASS_MAP = {char_class.value: char_class for char_class in CharClass}

NON_HUMANS = [CharClass.DWARF, CharClass.ELF, CharClass.HALFLING]
SPELLCASTERS = [CharClass.CLERIC, CharClass.MAGIC_USER, CharClass.ELF]
CHAOTICS = [CharClass.MAGIC_USER, CharClass.ELF]

HIT_DICE = {
    CharClass.CLERIC: 6,
    CharClass.FIGHTER: 8,
    CharClass.MAGIC_USER: 4,
    CharClass.SPECIALIST: 6,
    CharClass.DWARF: 10,
    CharClass.ELF: 6,
    CharClass.HALFLING: 6}

HIT_BONUSES = {
    CharClass.CLERIC: 2,
    CharClass.FIGHTER: 3,
    CharClass.MAGIC_USER: 1,
    CharClass.SPECIALIST: 2,
    CharClass.DWARF: 3,
    CharClass.ELF: 2,
    CharClass.HALFLING: 2}

MIN_HP = {
    CharClass.CLERIC: 4,
    CharClass.FIGHTER: 8,
    CharClass.MAGIC_USER: 3,
    CharClass.SPECIALIST: 4,
    CharClass.DWARF: 6,
    CharClass.ELF: 4,
    CharClass.HALFLING: 4}

# These correspond to Paralyze, Poison, Breath, Device, and Magic in the LotFP rules.
# The names are different to maintain compatibility with the remote generator.
SAVE_NAMES = ['stone', 'poison', 'breath', 'wands', 'magic']

# This is how often the saves change. As in, the saves change every X levels, and this
# is X.
SAVE_CHANGE_INTERVALS = {
    CharClass.CLERIC: 4,
    CharClass.FIGHTER: 3,
    CharClass.MAGIC_USER: 5,
    CharClass.SPECIALIST: 4,
    CharClass.DWARF: 3,
    CharClass.ELF: 3,
    CharClass.HALFLING: 2}

# In order to save space (and sanity), we're representing the saves as two-dimensional
# arrays, with one row for initial (level 1) values and further rows representing each
# time the saves change (4 to 6 times per class). This allows us to have 4-6 rows per
# class, rather than 17+.
LOTFP_SAVES = {
    CharClass.CLERIC: np.array(
        [[14, 11, 16, 12, 15],
         [-2, -2, -2, -2, -3],
         [-2, -2, -2, -2, -3],
         [-2, -4, -4, -4, -3],
         [-2, -1, -2, 0, -1]]),
    CharClass.FIGHTER: np.array(
        [[14, 12, 15, 13, 16],
         [-2, -2, -2, -2, -2],
         [-2, -2, -4, -2, -2],
         [-2, -2, -2, -2, -2],
         [-2, -2, -2, -2, -2]]),
    CharClass.MAGIC_USER: np.array(
        [[13, 13, 16, 13, 14],
         [-2, -2, -2, -2, -2],
         [-2, -2, -2, -2, -4],
         [-3, -2, -4, -4, -2],
         [-1, -1, -1, -1, -2]]),
    CharClass.SPECIALIST: np.array(
        [[14, 16, 15, 14, 14],
         [-3, -4, -1, -1, -2],
         [-2, -2, -2, -2, -2],
         [-2, -2, -2, -2, -2],
         [-2, -2, -2, -2, -2]]),
    CharClass.DWARF: np.array(
        [[10, 8, 13, 9, 12],
         [-2, -2, -3, -2, -2],
         [-2, -2, -3, -2, -2],
         [-2, -2, -3, -2, -2],
         [-2, 0, -2, -1, -2]]),
    # Elf saves have a dummy row of zeroes inserted to deal with their strange special
    # cases. Basically, level 16 does NOT have a change, even though dividing by the
    # save interval would suggest that it does. The easiest way to handle this (without
    # a lot of extra code) is to pad the array so that 16 does NOT change and 17 does.
    # This allows us to keep the special case code the same for all classes.
    CharClass.ELF: np.array(
        [[13, 12, 15, 13, 15],
         [-2, -2, -2, -2, -2],
         [-2, -2, -4, -2, -2],
         [-2, -2, -2, -2, -2],
         [-2, -2, -2, -2, -2],
         [0, 0, 0, 0, 0],
         [-2, -1, -2, -2, -2]]),
    CharClass.HALFLING: np.array(
        [[10, 8, 13, 9, 12],
         [-2, -2, -3, -2, -2],
         [-2, -2, -3, -2, -2],
         [-2, -2, -3, -2, -2],
         [-2, 0, -2, -1, -2]])
}

SKILL_POINTS_TO_SPEND = "You have {} skill points to spend."


class LotFPCharacter(object):
    def __init__(self,
                 desired_class=None,
                 desired_level=1,
                 calculate_encumbrance=True,
                 counter=1):
        self.details = tools.fetch_character(desired_class)
        # self.pcClass = self.details['class']
        self.pcClass = CLASS_MAP[self.details['class'].casefold()]
        self.level = desired_level
        self.calculate_encumbrance = calculate_encumbrance
        self.counter = counter

        self.name = '_'.join([str(self.counter + 1), self.pcClass.value])
        self.fdf_name = self.name + '.fdf'
        self.filled_name = self.name + '_Filled.pdf'

        self.alignment = self.align()
        self.attributes = {item[0]: item[1] for item in self.details['attributes']}
        self.mods = self.split_mods()
        self.hp = self.get_hp(self.level)
        self.saves = self.get_saves()

        self.skills = {item[0]: item[1] for item in self.details['skills']}
        if self.pcClass in NON_HUMANS and self.level > 1:
            self.get_nonhuman_skills()
        # Specialists get skill points to spend.
        if self.pcClass is CharClass.SPECIALIST:
            self.skill_points = 2 * (self.level - 1)
        else:
            self.skill_points = None

        self.equipment = tools.format_equipment_list(
            self.details,
            self.calculate_encumbrance)
        self.attacks = self.calculate_attack_bonuses()
        self.AC = self.calculate_armor_classes()

        # Lots of the entries in the original character details have
        # been reformatted, so we'll remove them.
        entries_to_reformat = [
            'attributes',
            'attr',
            'skills',
            'equipment',
            'saves',
            'ac']
        for item in entries_to_reformat:
            del self.details[item]

        # Nobody wants to see zeroes in their attribute modifiers.
        # If it's zero, we'll just leave it blank.
        self.mods = tools.clear_mod_zeroes(self.mods)

        if self.alignment is not None:
            self.details['alignment'] = self.alignment
        for field in ['level', 'hp']:
            self.details[field] = getattr(self, field)
        if self.skill_points:
            self.details['skill_points'] = SKILL_POINTS_TO_SPEND.format(self.skill_points)

        # We've gotta replace the removed character detail entries
        # with our nice reformatted ones.
        reformatted = [
            self.attributes,
            self.mods,
            self.saves,
            self.skills,
            self.equipment,
            self.attacks,
            self.AC]
        for item in reformatted:
            self.details = {**self.details, **item}

    def is_spellcaster(self):
        return self.pcClass in SPELLCASTERS

    def is_nonhuman(self):
        return self.pcClass in NON_HUMANS

    def is_special_case_for_saves(self):
        """
        Determine if the character's saves must be calculated by special case.

        Magic-User saves are special case at level 19+, Dwarf saves are special
        case at level 12+, and Elf saves are special case at level 16+.
        """
        return (self.pcClass is CharClass.MAGIC_USER and self.level >= 19) or \
               (self.pcClass is CharClass.DWARF and self.level >= 12) or \
               (self.pcClass is CharClass.ELF and self.level >= 17) or \
               (self.pcClass is CharClass.HALFLING)

    def align(self):
        alignment = None
        if self.pcClass is CharClass.CLERIC:
            alignment = 'Lawful'
        if self.pcClass in CHAOTICS:
            alignment = 'Chaotic'

        return alignment

    def split_mods(self):
        """
        Takes a dictionary of attributes and scores and returns a dictionary
        of attributes with modifiers only. If no scores have modifiers,
        returns keys with values set to 0.
        """
        dictofmods = {'CHAmod': "0",
                      'CONmod': "0",
                      'STRmod': "0",
                      'DEXmod': "0",
                      'INTmod': "0",
                      'WISmod': "0"}
        for key in self.details['attr']:
            attr_name = key
            value = self.details['attr'].get(key)
            modifier = value[value.find("(") + 1:value.find(")")]
            if '+' in modifier or '-' in modifier:
                dictofmods[attr_name + 'mod'] = modifier

        return dictofmods

    def get_hp(self, level, hp=0):
        """
        We're only generating our own hitpoints until the remote generator
        is fixed to use correct LotFP hitdice.
        :param level: The desired level of the character.
        :param hp: The current hit points of the character (defaults to 0).
        :return: The number of hit points the character has.
        """
        hit_die = HIT_DICE[self.pcClass]
        hit_bonus = HIT_BONUSES[self.pcClass]

        if level < 10:
            # Roll hitdice for all levels other than level 1...
            # Assuming the minimum you can gain is 1 HP, although it isn't explicitly
            # stated in the rulebook.
            for i in range(level - 1):
                hp += max(random.randint(1, hit_die) + int(self.mods['CONmod']), 1)

            # ...account for the irritating fact that Magic-Users (and ONLY Magic-Users)
            # have a d6 hit die at first level and a d4 at 2nd level and up...
            if self.pcClass is CharClass.MAGIC_USER:
                hit_die = 6
            # ...then add the final roll for level 1 or the minimum HP for the class,
            # whichever is higher.
            hp += max(
                random.randint(1, hit_die) + int(self.mods['CONmod']),
                MIN_HP[self.pcClass])

            return hp

        if level >= 10:
            # Add the hit point bonus once for each level past 9.
            hp += hit_bonus * (level - 9)

            # Dwarves keep adding their CON bonus even after level 10. No one else does.
            if self.pcClass is CharClass.DWARF:
                hp += int(self.mods['CONmod']) * (level - 9)

            # Recursively call this function for all the levels from 9 down
            return self.get_hp(9, hp)

    def get_saves(self):
        """
        Calculate save values for a given character class and level.
        :return: A dictionary of saves in the form 'poison': 12.
        """
        interval = SAVE_CHANGE_INTERVALS[self.pcClass]
        effective_level = self.level

        # Levels 19+ are special cases for Magic-Users, 12+ are special cases
        # for Dwarves, 17+ are special cases for Elves, and Halflings are a
        # PAIN IN THE ASS. Halflings change immediately at level 2 and then every two
        # levels thereafter.
        if self.is_special_case_for_saves():
            if self.pcClass is CharClass.HALFLING:
                effective_level += 1
            else:
                effective_level += interval

        # We're summing the appropriate rows of the array to get the new save values.
        # Since save changes mostly occur at a consistent interval (i.e., every
        # 4 levels, or every 3 levels, etc.), we can determine which rows need to be
        # summed by dividing level by interval and rounding. So we're slicing the
        # array (array[:NUMBER_OF_ROWS]), and then summing the rows of that slice
        # (.sum(0), the zero means sum across the row axis).
        end_row = math.ceil(effective_level / interval)
        changes_to_saves = LOTFP_SAVES[self.pcClass][:end_row].sum(0)
        saves = dict(zip(SAVE_NAMES, changes_to_saves.flat))

        # We're SUBTRACTING the mod from the save because you
        # have to roll over to save. A LOWER save is better.
        saves['magic'] -= int(self.mods['INTmod'])
        for save in ['poison', 'wands', 'stone', 'breath']:
            saves[save] -= int(self.mods['WISmod'])

        return saves

    def get_nonhuman_skills(self):
        if self.pcClass is CharClass.DWARF and "Architecture" in self.skills:
            self.skills['Architecture'] = min(2 + math.ceil(self.level / 3), 6)

        if self.pcClass is CharClass.ELF and "Search" in self.skills:
            self.skills['Search'] = min(1 + math.ceil(self.level / 3), 6)

        if self.pcClass is CharClass.HALFLING and "Bushcraft" in self.skills:
            self.skills['Bushcraft'] = min(2 + math.ceil(self.level / 3), 6)

    def calculate_attack_bonuses(self):
        if self.pcClass is CharClass.FIGHTER:
            base = min(2 + (self.level - 1), 10)
        else:
            base = 1

        melee_attack_bonus, ranged_attack_bonus = base, base

        melee_attack_bonus = int(self.mods['STRmod']) + base
        ranged_attack_bonus = int(self.mods['DEXmod']) + base

        attacks = {'MeleeBonus': melee_attack_bonus,
                   'RangedBonus': ranged_attack_bonus}

        return attacks

    def calculate_armor_classes(self):
        armor_classes = {}

        # Shields add +1 to AC in melee combat and +2 to AC in ranged combat. We're
        # setting the shield bonus to +1 if a shield is present to make it easier to
        # add and subtract from different AC values.
        if 'Shield' in self.equipment.values() or 'Shield ' in self.equipment.values():
            shield_bonus = 1
        else:
            shield_bonus = 0

        # self.details['ac'] already includes DEX modifier, armor worn, and +1 for
        # shield (shields add +1 for melee and +2 for ranged). Surprised AC means
        # no DEX bonus (for good or ill), no shield bonus, and an additional -2.
        armor_classes['surprised_ac'] = self.details['ac'] - int(self.mods['DEXmod']) - shield_bonus - 2
        armor_classes['melee_ac'] = self.details['ac']

        # We're subtracting the +1 melee AC bonus for the shield, if present.
        armor_classes['melee_ac_noshield'] = armor_classes['melee_ac'] - shield_bonus

        # Since self.details['ac'] ALREADY includes a +1 for the shield (if present), we
        # only need to add 1 to reach the required +2 ranged AC bonus for having
        # a shield.
        armor_classes['ranged_ac'] = self.details['ac'] + shield_bonus
        armor_classes['ranged_ac_noshield'] = armor_classes['ranged_ac'] - (2 * shield_bonus)

        return armor_classes
