import lament_mod.tools as tools
import random


HIT_DICE = {
    'Cleric': 6,
    'Fighter': 8,
    'Magic-User': 4,
    'Specialist': 6,
    'Dwarf': 10,
    'Elf': 6,
    'Halfling': 6}

HIT_BONUSES = {
    'Cleric': 2,
    'Fighter': 3,
    'Magic-User': 1,
    'Specialist': 2,
    'Dwarf': 3,
    'Elf': 2,
    'Halfling': 2}

MIN_HP = {
    'Cleric': 4,
    'Fighter': 8,
    'Magic-User': 3,
    'Specialist': 4,
    'Dwarf': 6,
    'Elf': 4,
    'Halfling': 4}

LOTFP_SAVES = {
    'Cleric': {'poison': 11, 'wands': 12, 'stone': 14, 'breath': 16, 'magic': 15},
    'Fighter': {'poison': 12, 'wands': 13, 'stone': 14, 'breath': 15, 'magic': 16},
    'Magic-User': {'poison': 13, 'wands': 13, 'stone': 13, 'breath': 16, 'magic': 14},
    'Specialist': {'poison': 16, 'wands': 14, 'stone': 14, 'breath': 15, 'magic': 14},
    'Dwarf': {'poison': 8, 'wands': 9, 'stone': 10, 'breath': 13, 'magic': 12},
    'Elf': {'poison': 12, 'wands': 13, 'stone': 13, 'breath': 15, 'magic': 15},
    'Halfling': {'poison': 8, 'wands': 9, 'stone': 10, 'breath': 13, 'magic': 12}}


class LotFPCharacter(object):
    def __init__(self,
                 desired_class=None,
                 desired_level=1,
                 calculate_encumbrance=True,
                 counter=1):
        self.details = tools.fetch_character(desired_class)
        self.counter = counter
        self.pcClass = self.details['class']
        self.level = desired_level

        self.name = '_'.join([str(self.counter + 1), self.pcClass])
        self.fdf_name = self.name + '.fdf'
        self.filled_name = self.name + '_Filled.pdf'

        self.alignment = self.align(self.pcClass)
        self.attributes = {item[0]: item[1] for item in self.details['attributes']}
        self.mods = self.split_mods(self.details['attr'])
        self.hp = self.get_hp(self.pcClass, self.mods, self.level)
        self.saves = self.get_saves(self.pcClass, self.mods)
        self.skills = {item[0]: item[1] for item in self.details['skills']}
        self.skill_points = 2 * (self.level - 1) if self.pcClass == "Specialist" else None

        self.calculate_encumbrance = calculate_encumbrance
        self.equipment = tools.format_equipment_list(
            self.details,
            self.calculate_encumbrance)
        self.attacks = self.calculate_attack_bonuses(self.mods, self.pcClass)
        self.AC = self.calculate_armor_classes(
            self.mods,
            self.equipment,
            self.details['ac'])

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
        for field in ['level', 'hp', 'skill_points']:
            self.details[field] = getattr(self, field)
        # self.details['level'] = self.level
        # self.details['hp'] = self.hp

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

    def align(self, pcClass=None):
        alignment = None
        if pcClass.casefold() == 'Cleric'.casefold():
            alignment = 'Lawful'
        if pcClass.casefold() in ('Magic-User'.casefold(), 'Elf'.casefold()):
            alignment = 'Chaotic'

        return alignment

    def split_mods(self, attributes):
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
        for key in attributes:
            attr_name = key
            value = attributes.get(key)
            modifier = value[value.find("(") + 1:value.find(")")]
            if '+' in modifier or '-' in modifier:
                dictofmods[attr_name + 'mod'] = modifier

        return dictofmods

    def get_hp(self, pcClass, mods, level, hp=0):
        """
        We're only generating our own hitpoints until the remote generator
        is fixed to use correct LotFP hitdice.
        :param pcClass: The character class of the character.
        :param mods: The attribute modifiers of the character.
        :param level: The desired level of the character.
        :param hp: The current hit points of the character (defaults to 0).
        :return: The number of hit points the character has.
        """
        hit_die = HIT_DICE[pcClass]
        hit_bonus = HIT_BONUSES[pcClass]

        if level < 10:
            # Roll hitdice for all levels other than level 1...
            # Assuming the minimum you can gain is 1 HP, although it isn't explicitly
            # stated in the rulebook.
            for i in range(level - 1):
                hp += max(random.randint(1, hit_die) + int(mods['CONmod']), 1)

            # ...account for the irritating fact that Magic-Users (and ONLY Magic-Users)
            # have a d6 hit die at first level and a d4 at 2nd level and up...
            if pcClass.casefold() in "Magic-User".casefold():
                hit_die = 6
            # ...then add the final roll for level 1 or the minimum HP for the class,
            # whichever is higher.
            hp += max(random.randint(1, hit_die) + int(mods['CONmod']), MIN_HP[pcClass])

            return hp

        if level >= 10:
            # Add the hit point bonus once for each level past 9.
            hp += hit_bonus * (level - 9)

            # Dwarves keep adding their CON bonus even after level 10. No one else does.
            if pcClass.casefold() in "Dwarf".casefold():
                hp += int(mods['CONmod']) * (level - 9)

            # Recursively call this function for all the levels from 9 down
            return self.get_hp(pcClass, mods, 9, hp)

    def get_saves(self, pcClass, mods):
        """
        We're only generating our own saves until the remote generator\
        is fixed to return the right LotFP saves.

        :param pcClass: The character class of the character.
        :param mods: The attribute modifiers of the character.
        :return: A dictionary of saves in the form 'poison': 12.
        """
        saves = LOTFP_SAVES[pcClass]

        # We're SUBTRACTING the mod from the save because you
        # have to roll over to save. A LOWER save is better.
        saves['magic'] -= int(mods['INTmod'])
        for save in ['poison', 'wands', 'stone', 'breath']:
            saves[save] -= int(mods['WISmod'])

        return saves

    def calculate_attack_bonuses(self, mods, pcClass=None):
        if pcClass == 'Fighter':
            base = 2
        else:
            base = 1

        melee_attack_bonus, ranged_attack_bonus = base, base

        melee_attack_bonus = int(mods['STRmod']) + base
        ranged_attack_bonus = int(mods['DEXmod']) + base

        attacks = {'MeleeBonus': melee_attack_bonus,
                   'RangedBonus': ranged_attack_bonus}

        return attacks

    def calculate_armor_classes(self, mods, equipment, original_ac=12):
        armor_classes = {}
        if 'Shield' in equipment.values() or 'Shield ' in equipment.values():
            shield_bonus = 1
        else:
            shield_bonus = 0

        # original_AC already includes DEX modifier and armor worn,
        # but not shield. Surprised AC means no DEX bonus, no shield,
        # and an additional -2.
        armor_classes['surprised_ac'] = original_ac - int(mods['DEXmod']) - 2
        armor_classes['melee_ac'] = original_ac + shield_bonus
        armor_classes['melee_ac_noshield'] = armor_classes['melee_ac'] - shield_bonus
        armor_classes['ranged_ac'] = original_ac + (2 * shield_bonus)
        armor_classes['ranged_ac_noshield'] = armor_classes['ranged_ac'] - (2 * shield_bonus)

        return armor_classes
