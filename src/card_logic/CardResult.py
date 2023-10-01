from src import constants
from src.card_logic import calculate_win_rate, card_colors, field_process_sort, logger


import numpy


import copy


class CardResult:
    """This class processes a card list and produces results based on a list of fields (i.e., ALSA, GIHWR, COLORS, etc.)"""

    def __init__(self, set_metrics, tier_data, configuration, pick_number):
        self.metrics = set_metrics
        self.tier_data = tier_data
        self.configuration = configuration
        self.pick_number = pick_number

    def return_results(self, card_list, colors, fields):
        """This function processes a card list and returns a list with the requested field results"""
        return_list = []
        wheel_sum = 0
        if constants.DATA_FIELD_WHEEL in fields.values():
            wheel_sum = self.__retrieve_wheel_sum(card_list)

        for card in card_list:
            try:
                selected_card = copy.deepcopy(card)
                selected_card["results"] = ["NA"] * len(fields)

                for count, option in enumerate(fields.values()):
                    if constants.FILTER_OPTION_TIER in option:
                        selected_card["results"][count] = self.__process_tier(
                            card, option)
                    elif option == constants.DATA_FIELD_COLORS:
                        selected_card["results"][count] = self.__process_colors(
                            card)
                    elif option == constants.DATA_FIELD_WHEEL:
                        selected_card["results"][count] = self.__process_wheel_normalized(
                            card, wheel_sum)
                    elif option in card:
                        selected_card["results"][count] = card[option]
                    else:
                        selected_card["results"][count] = self.__process_filter_fields(
                            card, option, colors)

                return_list.append(selected_card)
            except Exception as error:
                logger.error(error)
        return return_list

    def __process_tier(self, card, option):
        """Retrieve tier list rating for this card"""
        result = "NA"
        try:
            card_name = card[constants.DATA_FIELD_NAME].split(" // ")
            if card_name[0] in self.tier_data[option][constants.DATA_SECTION_RATINGS]:
                tier_data = self.tier_data[option][constants.DATA_SECTION_RATINGS][card_name[0]]
                result = tier_data["rating"]
                # Append an asterisk to denote a comment
                result = "*" + result if tier_data["comment"] else result
        except Exception as error:
            logger.error(error)

        return result

    def __process_colors(self, card):
        """Retrieve card colors based on color identity (includes kicker, abilities, etc.) or mana cost"""
        result = "NA"

        try:
            if self.configuration.settings.color_identity_enabled:
                result = "".join(card[constants.DATA_FIELD_COLORS])
            elif constants.CARD_TYPE_LAND in card[constants.DATA_FIELD_TYPES]:
                # For lands, the card mana cost can't be used to identify the card colors
                result = "".join(card[constants.DATA_FIELD_COLORS])
            else:
                result = "".join(
                    list(card_colors(card[constants.DATA_FIELD_MANA_COST]).keys()))
        except Exception as error:
            logger.error(error)

        return result

    def __retrieve_wheel_sum(self, card_list):
        """Calculate the sum of all wheel percentage values for the card list"""
        total_sum = 0

        for card in card_list:
            total_sum += self.__process_wheel(card)

        return total_sum

    def __process_wheel(self, card):
        """Calculate wheel percentage"""
        result = 0

        try:
            if self.pick_number <= len(constants.WHEEL_COEFFICIENTS):
                # 0 is treated as pick 1 for PremierDraft P1P1
                self.pick_number = max(self.pick_number, 1)
                alsa = card[constants.DATA_FIELD_DECK_COLORS][constants.FILTER_OPTION_ALL_DECKS][constants.DATA_FIELD_ALSA]
                coefficients = constants.WHEEL_COEFFICIENTS[self.pick_number - 1]
                # Exclude ALSA values below 2
                result = round(numpy.polyval(coefficients, alsa),
                               1) if alsa >= 2 else 0
                result = max(result, 0)
        except Exception as error:
            logger.error(error)

        return result

    def __process_wheel_normalized(self, card, total_sum):
        """Calculate the normalized wheel percentage using the sum of all percentages within the card list"""
        result = 0

        try:
            result = self.__process_wheel(card)

            result = round((result / total_sum)*100, 1) if total_sum > 0 else 0
        except Exception as error:
            logger.error(error)

        return result

    def __process_filter_fields(self, card, option, colors):
        """Retrieve win rate result based on the application settings"""
        result = "NA"

        try:
            rated_colors = []
            for color in colors:
                if constants.DATA_FIELD_DECK_COLORS in card \
                        and color in card[constants.DATA_FIELD_DECK_COLORS] \
                        and option in card[constants.DATA_FIELD_DECK_COLORS][color]:
                    if option in constants.WIN_RATE_OPTIONS:
                        rating_data = self.__format_win_rate(card,
                                                             option,
                                                             constants.WIN_RATE_FIELDS_DICT[option],
                                                             color)
                        rated_colors.append(rating_data)
                    else:  # Field that's not a win rate (ALSA, IWD, etc)
                        result = card[constants.DATA_FIELD_DECK_COLORS][color][option]
            if rated_colors:
                result = sorted(
                    rated_colors, key=field_process_sort, reverse=True)[0]
        except Exception as error:
            logger.error(error)

        return result

    def __format_win_rate(self, card, winrate_field, winrate_count, color):
        """The function will return a grade, rating, or win rate depending on the application's Result Format setting"""
        result = 0
        # Produce a result that matches the Result Format setting
        if self.configuration.settings.result_format == constants.RESULT_FORMAT_RATING:
            result = self.__card_rating(
                card, winrate_field, winrate_count, color)
        elif self.configuration.settings.result_format == constants.RESULT_FORMAT_GRADE:
            result = self.__card_grade(
                card, winrate_field, winrate_count, color)
        else:
            result = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color][winrate_field],
                                        card[constants.DATA_FIELD_DECK_COLORS][color][winrate_count],
                                        self.configuration.settings.bayesian_average_enabled)

        return result

    def __card_rating(self, card, winrate_field, winrate_count, color):
        """The function will take a card's win rate and calculate a 5-point rating"""
        result = 0
        try:
            winrate = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color][winrate_field],
                                         card[constants.DATA_FIELD_DECK_COLORS][color][winrate_count],
                                         self.configuration.settings.bayesian_average_enabled)

            deviation_list = list(constants.GRADE_DEVIATION_DICT.values())
            upper_limit = self.metrics.mean + \
                self.metrics.standard_deviation * deviation_list[0]
            lower_limit = self.metrics.mean + \
                self.metrics.standard_deviation * deviation_list[-1]

            if (winrate != 0) and (upper_limit != lower_limit):
                result = round(
                    ((winrate - lower_limit) / (upper_limit - lower_limit)) * 5.0, 1)
                result = min(result, 5.0)
                result = max(result, 0)

        except Exception as error:
            logger.error(error)
        return result

    def __card_grade(self, card, winrate_field, winrate_count, color):
        """The function will take a card's win rate and assign a letter grade based on the number of standard deviations from the mean"""
        result = constants.LETTER_GRADE_NA
        try:
            winrate = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color][winrate_field],
                                         card[constants.DATA_FIELD_DECK_COLORS][color][winrate_count],
                                         self.configuration.settings.bayesian_average_enabled)

            if ((winrate != 0) and (self.metrics.standard_deviation != 0)):
                result = constants.LETTER_GRADE_F
                for grade, deviation in constants.GRADE_DEVIATION_DICT.items():
                    standard_score = (
                        winrate - self.metrics.mean) / self.metrics.standard_deviation
                    if standard_score >= deviation:
                        result = grade
                        break

        except Exception as error:
            logger.error(error)
        return result