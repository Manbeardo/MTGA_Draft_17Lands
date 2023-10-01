"""This module contains the functions that are used for processing the collected cards"""
from itertools import combinations
import logging
import math
from src import constants
from src.card_logic.DeckMetrics import DeckMetrics
from src.logger import create_logger

logger = create_logger()


def field_process_sort(field_value):
    """This function collects the numeric order of a letter grade for the purpose of sorting"""
    processed_value = field_value

    try:
        # Remove the tier asterisks before sorting
        if isinstance(field_value, str):
            field_value = field_value.replace('*', '')
        if field_value in constants.GRADE_ORDER_DICT:
            processed_value = constants.GRADE_ORDER_DICT[field_value]
    except ValueError:
        pass
    return processed_value


def format_tier_results(value, old_format, new_format):
    """This function converts the tier list ratings, from old tier lists, back to letter grades"""
    new_value = value
    try:
        # ratings to grades
        if (old_format == constants.RESULT_FORMAT_RATING) and (new_format == constants.RESULT_FORMAT_GRADE):
            new_value = constants.LETTER_GRADE_NA
            for grade, threshold in constants.TIER_CONVERSION_RATINGS_GRADES_DICT.items():
                if value > threshold:
                    new_value = grade
                    break
    except Exception as error:
        logger.error(error)

    return new_value


def deck_card_search(deck, search_colors, card_types, include_types, include_colorless, include_partial):
    """This function retrieves a subset of cards that meet certain criteria (type, color, etc.)"""
    card_color_sorted = {}
    main_color = ""
    combined_cards = []
    for card in deck:
        try:
            colors = list(card_colors(
                card[constants.DATA_FIELD_MANA_COST]).keys())

            if constants.CARD_TYPE_LAND in card[constants.DATA_FIELD_TYPES]:
                colors = card[constants.DATA_FIELD_COLORS]

            if colors and (set(colors) <= set(search_colors)):
                main_color = colors[0]

                if ((include_types and any(x in card[constants.DATA_FIELD_TYPES] for x in card_types)) or
                   (not include_types and not any(x in card[constants.DATA_FIELD_TYPES] for x in card_types))):

                    if main_color not in card_color_sorted:
                        card_color_sorted[main_color] = []

                    card_color_sorted[main_color].append(card)

            elif set(search_colors).intersection(colors) and include_partial:
                for color in colors:
                    if ((include_types and any(x in card[constants.DATA_FIELD_TYPES] for x in card_types)) or
                       (not include_types and not any(x in card[constants.DATA_FIELD_TYPES] for x in card_types))):

                        if color not in card_color_sorted:
                            card_color_sorted[color] = []

                        card_color_sorted[color].append(card)

            if not colors and include_colorless:

                if ((include_types and any(x in card[constants.DATA_FIELD_TYPES] for x in card_types)) or
                   (not include_types and not any(x in card[constants.DATA_FIELD_TYPES] for x in card_types))):

                    combined_cards.append(card)
        except Exception as error:
            logger.error(error)

    for key, value in card_color_sorted.items():
        if key in search_colors:
            combined_cards.extend(value)

    return combined_cards


def deck_metrics(deck):
    """This function determines the total CMC, count, and distribution of a collection of cards"""
    metrics = DeckMetrics()
    cmc_total = 0
    try:

        metrics.total_cards = len(deck)

        for card in deck:
            if any(x in [constants.CARD_TYPE_CREATURE]
                   for x in card[constants.DATA_FIELD_TYPES]):
                metrics.creature_count += 1
                metrics.total_non_land_cards += 1
                cmc_total += card[constants.DATA_FIELD_CMC]

                index = int(
                    min(card[constants.DATA_FIELD_CMC],
                        len(metrics.distribution_creatures) - 1))
                metrics.distribution_creatures[index] += 1
            else:
                if constants.CARD_TYPE_LAND not in card[constants.DATA_FIELD_TYPES]:
                    cmc_total += card[constants.DATA_FIELD_CMC]
                    metrics.total_non_land_cards += 1
                    index = int(
                        min(card[constants.DATA_FIELD_CMC],
                            len(metrics.distribution_noncreatures) - 1))
                    metrics.distribution_noncreatures[index] += 1
                metrics.noncreature_count += 1

            index = int(
                min(card[constants.DATA_FIELD_CMC],
                    len(metrics.distribution_all) - 1))
            metrics.distribution_all[index] += 1

        metrics.cmc_average = (cmc_total / metrics.total_non_land_cards
                               if metrics.total_non_land_cards
                               else 0.0)

    except Exception as error:
        logger.error(error)

    return metrics


def option_filter(deck, option_selection, metrics, configuration):
    """This function returns a list of colors based on the deck filter option"""
    filtered_color_list = [option_selection]
    try:
        if constants.FILTER_OPTION_AUTO in option_selection:
            filtered_color_list = auto_colors(deck, 5, metrics, configuration)
        else:
            filtered_color_list = [option_selection]
    except Exception as error:
        logger.error(error)
    return filtered_color_list


def deck_colors(deck, colors_max, metrics, configuration):
    """This function determines the prominent colors for a collection of cards"""
    colors_result = {}
    try:
        threshold = metrics.mean - 0.33 * metrics.standard_deviation
        colors = calculate_color_affinity(
            deck, constants.FILTER_OPTION_ALL_DECKS, threshold, configuration)

        # Modify the dictionary to include ratings
        color_list = list(
            map((lambda x: {"color": x, "rating": colors[x]}), colors.keys()))

        # Sort the list by decreasing ratings
        color_list = sorted(
            color_list, key=lambda k: k["rating"], reverse=True)

        # Remove extra colors beyond limit
        color_list = color_list[0:colors_max]

        # Return colors
        sorted_colors = list(map((lambda x: x["color"]), color_list))

        # Create color permutation
        color_combination = []

        for count in range(colors_max + 1):
            if count > 1:
                color_combination.extend(combinations(sorted_colors, count))
            else:
                color_combination.extend((sorted_colors))

        # Convert tuples to list of strings
        color_strings = [''.join(tups) for tups in color_combination]
        color_strings = [x for x in color_strings if len(x) <= colors_max]

        color_strings = list(set(color_strings))

        color_dict = {}
        for color_string in color_strings:
            for color in color_string:
                if color_string not in color_dict:
                    color_dict[color_string] = 0
                color_dict[color_string] += colors[color]

        for color_option in constants.DECK_COLORS:
            for key, value in color_dict.items():
                if (len(key) == len(color_option)) and set(key).issubset(color_option):
                    colors_result[color_option] = value

        # Recalculate values based on the filtered win rates
        for color in colors_result:
            base_rating = calculate_color_rating(deck,
                                                 color,
                                                 threshold,
                                                 configuration)
            curve_factor = calculate_curve_factor(deck,
                                                  color,
                                                  configuration)
            colors_result[color] = base_rating * curve_factor

        # Add All Decks as a baseline
        colors_result[constants.FILTER_OPTION_ALL_DECKS] = calculate_color_rating(deck,
                                                                                  constants.FILTER_OPTION_ALL_DECKS,
                                                                                  metrics.mean,
                                                                                  configuration)
        colors_result = dict(
            sorted(colors_result.items(), key=lambda item: item[1], reverse=True))
    except Exception as error:
        logger.error(error)

    return colors_result


def auto_colors(deck, colors_max, metrics, configuration):
    """When the Auto deck filter is selected, this function identifies the prominent color pairs from the collected cards"""
    try:
        deck_colors_list = [constants.FILTER_OPTION_ALL_DECKS]
        colors_dict = {}
        deck_length = len(deck)
        if deck_length > 15:
            colors_dict = deck_colors(deck, colors_max, metrics, configuration)
            colors = list(colors_dict.keys())
            auto_select_threshold = max(70 - deck_length, 25)
            if len(colors) >= 2:
                if (colors_dict[colors[0]] - colors_dict[colors[1]]) > auto_select_threshold:
                    deck_colors_list = colors[0:1]
                elif configuration.settings.auto_highest_enabled:
                    deck_colors_list = colors[0:2]

    except Exception as error:
        logger.error(error)

    return deck_colors_list


def calculate_color_rating(cards, color_filter, threshold, configuration):
    """This function identifies the main deck colors based on the GIHWR of the collected cards"""
    rating = 0

    for card in cards:
        try:
            if color_filter in card[constants.DATA_FIELD_DECK_COLORS]:
                gihwr = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIHWR],
                                           card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIH],
                                           configuration.settings.bayesian_average_enabled)
                if gihwr > threshold:
                    rating += gihwr - threshold
        except Exception as error:
            logger.error(error)
    return rating


def sort_cards_win_rate(cards, filter_order, bayesian_enabled):
    """This function will acquire a non-zero win rate for each card and sort the cards by the win rate (highest to lowest)"""
    for card in cards:
        card["results"] = [0]
        try:
            for color_filter in filter_order:
                win_rate = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIHWR],
                                              card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIH],
                                              bayesian_enabled)
                if win_rate:
                    card["results"] = [win_rate]
                    break

        except Exception as error:
            logger.error(error)

    sorted_cards = sorted(
        cards, key=lambda k: k["results"][0], reverse=True)

    return sorted_cards


def calculate_curve_factor(deck, color_filter, configuration):
    """This function will assign a rating to a collection of cards based on how well they meet the deck building requirements"""
    curve_levels = [.10, .10, .10, .10, .15,
                    .15, .15, .20, .20, .20,
                    .25, .25, .25, .30, .30,
                    .30, .30, .40, .40, .40]

    curve_start = 15
    pick_number = len(deck)
    index = max(pick_number - curve_start, 0)
    curve_level = 0.0
    curve_factor = 0.0
    base_curve_factor = 1.0
    minimum_creature_count = configuration.card_logic.minimum_creatures

    try:
        filtered_cards = deck_card_search(
            deck,
            color_filter,
            constants.CARD_TYPE_DICT[constants.CARD_TYPE_SELECTION_NON_LANDS][0],
            True,
            True,
            False)
        deck_info = deck_metrics(filtered_cards)
        curve_level = curve_levels[int(
            min(index, len(curve_levels) - 1))]

        if deck_info.total_cards < configuration.card_logic.deck_control.maximum_card_count:
            curve_factor -= ((configuration.card_logic.deck_control.maximum_card_count - deck_info.creature_count)
                             / configuration.card_logic.deck_control.maximum_card_count) * curve_level
        elif deck_info.creature_count < minimum_creature_count:
            curve_factor = (deck_info.creature_count
                            / minimum_creature_count) * curve_level
        else:
            curve_factor = curve_level

    except Exception as error:
        logger.error(error)

    return base_curve_factor + curve_factor


def calculate_color_affinity(deck_cards, color_filter, threshold, configuration):
    """This function identifies the main deck colors based on the GIHWR of the collected cards"""
    colors = {}

    for card in deck_cards:
        try:
            if color_filter in card[constants.DATA_FIELD_DECK_COLORS]:
                gihwr = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIHWR],
                                           card[constants.DATA_FIELD_DECK_COLORS][color_filter][constants.DATA_FIELD_GIH],
                                           configuration.settings.bayesian_average_enabled)
                if gihwr > threshold:
                    mana_colors = card_colors(
                        card[constants.DATA_FIELD_MANA_COST])
                    for color in mana_colors:
                        if color not in colors:
                            colors[color] = 0
                        colors[color] += (gihwr - threshold)
        except Exception as error:
            logger.error(error)
    return colors


def row_color_tag(mana_cost):
    """This function selects the color tag for a table row based on a card's mana cost"""
    colors = list(card_colors(mana_cost).keys())

    row_tag = constants.CARD_ROW_COLOR_COLORLESS_TAG
    if len(colors) > 1:
        row_tag = constants.CARD_ROW_COLOR_GOLD_TAG
    elif constants.CARD_COLOR_SYMBOL_RED in colors:
        row_tag = constants.CARD_ROW_COLOR_RED_TAG
    elif constants.CARD_COLOR_SYMBOL_BLUE in colors:
        row_tag = constants.CARD_ROW_COLOR_BLUE_TAG
    elif constants.CARD_COLOR_SYMBOL_BLACK in colors:
        row_tag = constants.CARD_ROW_COLOR_BLACK_TAG
    elif constants.CARD_COLOR_SYMBOL_WHITE in colors:
        row_tag = constants.CARD_ROW_COLOR_WHITE_TAG
    elif constants.CARD_COLOR_SYMBOL_GREEN in colors:
        row_tag = constants.CARD_ROW_COLOR_GREEN_TAG
    return row_tag


def calculate_mean(cards, bayesian_enabled):
    """The function calculates the mean win rate of a collection of cards"""
    card_count = 0
    card_sum = 0
    mean = 0
    for card in cards:
        try:
            winrate = calculate_win_rate(cards[card][constants.DATA_FIELD_DECK_COLORS][constants.FILTER_OPTION_ALL_DECKS][constants.DATA_FIELD_GIHWR],
                                         cards[card][constants.DATA_FIELD_DECK_COLORS][constants.FILTER_OPTION_ALL_DECKS][constants.DATA_FIELD_GIH],
                                         bayesian_enabled)

            if winrate == 0:
                continue

            card_sum += winrate
            card_count += 1

        except Exception as error:
            logger.error(error)

    mean = float(card_sum / card_count) if card_count else 0

    return mean


def calculate_standard_deviation(cards, mean, bayesian_enabled):
    """The function calculates the standard deviation from the win rate of a collection of cards"""
    standard_deviation = 0
    card_count = 0
    sum_squares = 0
    for card in cards:
        try:
            winrate = calculate_win_rate(cards[card][constants.DATA_FIELD_DECK_COLORS][constants.FILTER_OPTION_ALL_DECKS][constants.DATA_FIELD_GIHWR],
                                         cards[card][constants.DATA_FIELD_DECK_COLORS][constants.FILTER_OPTION_ALL_DECKS][constants.DATA_FIELD_GIH],
                                         bayesian_enabled)

            if winrate == 0:
                continue

            squared_deviations = (winrate - mean) ** 2

            sum_squares += squared_deviations
            card_count += 1

        except Exception as error:
            logger.error(error)

    # Find the variance
    variance = (sum_squares / (card_count - 1)) if card_count > 2 else 0

    standard_deviation = math.sqrt(variance)

    return standard_deviation


def ratings_limits(cards, bayesian_enabled):
    """The function identifies the upper and lower win rates from a collection of cards"""
    upper_limit = 0
    lower_limit = 100

    for card in cards:
        for color in constants.DECK_COLORS:
            try:
                if color in cards[card][constants.DATA_FIELD_DECK_COLORS]:
                    gihwr = calculate_win_rate(cards[card][constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIHWR],
                                               cards[card][constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIH],
                                               bayesian_enabled)
                    if gihwr > upper_limit:
                        upper_limit = gihwr
                    if gihwr < lower_limit and gihwr != 0:
                        lower_limit = gihwr
            except Exception as error:
                logger.error(error)

    return upper_limit, lower_limit


def calculate_win_rate(winrate, count, bayesian_enabled):
    """The function will modify a card's win rate by applying the Bayesian Average algorithm or by zeroing a value with a low sample size"""
    calculated_winrate = 0.0
    try:
        calculated_winrate = winrate

        if bayesian_enabled:
            win_count = winrate * count
            # Bayesian average calculation
            calculated_winrate = (win_count + 1000) / (count + 20)
            calculated_winrate = round(calculated_winrate, 2)
        else:
            # Drop values that have fewer than 200 samples (same as 17Lands card_ratings page)
            if count < 200:
                calculated_winrate = 0.0
    except Exception as error:
        logger.error(error)
    return calculated_winrate


def deck_color_stats(deck, color):
    """The function will identify the number of creature and noncreature cards in a collection of cards"""
    creature_count = 0
    noncreature_count = 0

    try:
        creature_cards = deck_card_search(
            deck, color, [constants.CARD_TYPE_CREATURE], True, True, False)
        noncreature_cards = deck_card_search(
            deck, color, [constants.CARD_TYPE_CREATURE], False, True, False)
        noncreature_cards = deck_card_search(
            noncreature_cards, color,
            [constants.CARD_TYPE_INSTANT,
             constants.CARD_TYPE_SORCERY,
             constants.CARD_TYPE_ARTIFACT,
             constants.CARD_TYPE_ENCHANTMENT,
             constants.CARD_TYPE_PLANESWALKER], True, True, False)

        creature_count = len(creature_cards)
        noncreature_count = len(noncreature_cards)

    except Exception as error:
        logger.error(error)

    return creature_count, noncreature_count


def card_cmc_search(deck, offset, starting_cmc, cmc_limit, remaining_count):
    """The function will use recursion to search through a collection of cards and produce a list of cards with a mean CMC that is below a specific limit"""
    cards = []
    unused = []
    try:
        for count, card in enumerate(deck[offset:]):
            card_cmc = card[constants.DATA_FIELD_CMC]

            if card_cmc + starting_cmc <= cmc_limit:
                card_cmc += starting_cmc
                current_offset = offset + count
                current_remaining = int(max(remaining_count - 1, 0))
                if current_remaining == 0:
                    cards.append(card)
                    unused.extend(deck[current_offset + 1:])
                    break
                elif current_offset > (len(deck) - remaining_count):
                    unused.extend(deck[current_offset:])
                    break
                else:
                    current_offset += 1
                    cards, skipped = card_cmc_search(
                        deck, current_offset, card_cmc, cmc_limit, current_remaining)
                    if cards:
                        cards.append(card)
                        unused.extend(skipped)
                        break
                    else:
                        unused.append(card)
            else:
                unused.append(card)
    except Exception as error:
        logger.error(error)

    return cards, unused


def deck_rating(deck, deck_type, color, threshold, bayesian_enabled):
    """The function will produce a deck rating based on the combined GIHWR value for each card with a GIHWR value above a certain threshold"""
    rating = 0
    try:
        # Combined GIHWR of the cards
        for card in deck:
            try:
                gihwr = calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIHWR],
                                           card[constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIH],
                                           bayesian_enabled)
                if gihwr > threshold:
                    rating += gihwr
            except Exception:
                pass

        # Deck contains the recommended number of creatures
        recommended_creature_count = deck_type.recommended_creature_count
        filtered_cards = deck_card_search(
            deck, color, [constants.CARD_TYPE_CREATURE], True, True, False)

        if len(filtered_cards) < recommended_creature_count:
            rating -= (recommended_creature_count - len(filtered_cards)) * 50

        # Average CMC of the creatures is below the ideal cmc average
        cmc_average = deck_type.cmc_average
        total_cards = len(filtered_cards)
        total_cmc = 0

        for card in filtered_cards:
            total_cmc += card[constants.DATA_FIELD_CMC]

        cmc = total_cmc / total_cards

        if cmc > cmc_average:
            rating -= 500

        # Cards fit distribution
        minimum_distribution = deck_type.distribution
        distribution = [0, 0, 0, 0, 0, 0, 0]
        for card in filtered_cards:
            index = int(min(card[constants.DATA_FIELD_CMC],
                        len(minimum_distribution) - 1))
            distribution[index] += 1

    except Exception as error:
        logger.error(error)

    rating = int(rating)

    return rating


def copy_deck(deck, sideboard):
    """The function will produce a deck/sideboard list that is formatted in such a way that it can be copied to Arena and Sealdeck.tech"""
    deck_copy = ""
    try:
        # Copy Deck
        deck_copy = "Deck\n"
        # identify the arena_id for the cards
        for card in deck:
            deck_copy += f"{card[constants.DATA_FIELD_COUNT]} {card[constants.DATA_FIELD_NAME]}\n"

        # Copy sideboard
        if sideboard is not None:
            deck_copy += "\nSideboard\n"
            for card in sideboard:
                deck_copy += f"{card[constants.DATA_FIELD_COUNT]} {card[constants.DATA_FIELD_NAME]}\n"

    except Exception as error:
        logger.error(error)

    return deck_copy


def stack_cards(cards):
    """The function will produce a list consisting of unique cards and the number of copies of each card"""
    deck = {}
    deck_list = []
    for card in cards:
        try:
            name = card[constants.DATA_FIELD_NAME]
            if name not in deck:
                deck[name] = {constants.DATA_FIELD_COUNT: 1}
                for data_field in constants.DATA_SET_FIELDS:
                    if data_field in card:
                        deck[name][data_field] = card[data_field]
            else:
                deck[name][constants.DATA_FIELD_COUNT] += 1
        except Exception as error:
            logger.error(error)
    # Convert to list format
    deck_list = list(deck.values())

    return deck_list


def card_colors(mana_cost):
    """The function parses a mana cost string and returns a list of mana symbols"""
    colors = {}
    try:
        for color in constants.CARD_COLORS:
            if color in mana_cost:
                if color not in colors:
                    colors[color] = 1
                else:
                    colors[color] += 1

    except Exception as error:
        logger.error(error)
    return colors


def color_splash(cards, colors, splash_threshold, configuration):
    """The function will parse a list of cards to determine if there are any cards that might justify a splash"""
    color_affinity = {}
    splash_color = ""
    try:
        # Calculate affinity to rank colors based on splash threshold (minimum GIHWR)
        color_affinity = calculate_color_affinity(
            cards, colors, splash_threshold, configuration)

        # Modify the dictionary to include ratings
        color_affinity = list(
            map((lambda x: {"color": x, "rating": color_affinity[x]}), color_affinity.keys()))
        # Remove the current colors
        filtered_colors = color_affinity[:]
        for color in color_affinity:
            if color["color"] in colors:
                filtered_colors.remove(color)
        # Sort the list by decreasing ratings
        filtered_colors = sorted(
            filtered_colors, key=lambda k: k["rating"], reverse=True)

        if filtered_colors:
            splash_color = filtered_colors[0]["color"]
    except Exception as error:
        logger.error(error)
    return splash_color


def mana_base(deck):
    """The function will identify the number of lands that are needed to fill out a deck"""
    maximum_deck_size = 40
    combined_deck = []
    mana_types = {"Swamp": {"color": constants.CARD_COLOR_SYMBOL_BLACK, constants.DATA_FIELD_COUNT: 0},
                  "Forest": {"color": constants.CARD_COLOR_SYMBOL_GREEN, constants.DATA_FIELD_COUNT: 0},
                  "Mountain": {"color": constants.CARD_COLOR_SYMBOL_RED, constants.DATA_FIELD_COUNT: 0},
                  "Island": {"color": constants.CARD_COLOR_SYMBOL_BLUE, constants.DATA_FIELD_COUNT: 0},
                  "Plains": {"color": constants.CARD_COLOR_SYMBOL_WHITE, constants.DATA_FIELD_COUNT: 0}}
    total_count = 0
    try:
        number_of_lands = 0 if maximum_deck_size < len(
            deck) else maximum_deck_size - len(deck)

        # Go through the cards and count the mana types
        for card in deck:
            if constants.CARD_TYPE_LAND in card[constants.DATA_FIELD_TYPES]:
                # Subtract symbol for lands
                for mana_type in mana_types.values():
                    mana_type[constants.DATA_FIELD_COUNT] -= (1 if (mana_type["color"] in card[constants.DATA_FIELD_COLORS])
                                                              else 0)
            else:
                # Increase count for abilities that are not part of the mana cost
                mana_count = card_colors(card[constants.DATA_FIELD_MANA_COST])
                # for color in card[constants.DATA_FIELD_COLORS]:
                #    mana_count[color] = (
                #        mana_count[color] + 1) if color in mana_count else 1

                for mana_type in mana_types.values():
                    color = mana_type["color"]
                    mana_type[constants.DATA_FIELD_COUNT] += mana_count[color] if color in mana_count else 0

        for land in mana_types.values():
            land[constants.DATA_FIELD_COUNT] = max(
                land[constants.DATA_FIELD_COUNT], 0)
            total_count += land[constants.DATA_FIELD_COUNT]

        # Sort by lowest count
        mana_types = dict(
            sorted(mana_types.items(), key=lambda t: t[1][constants.DATA_FIELD_COUNT]))
        # Add x lands with a distribution set by the mana types
        total_lands = number_of_lands
        for land in mana_types:
            if not total_lands or not mana_types[land][constants.DATA_FIELD_COUNT]:
                continue

            land_count = int(math.ceil(
                (mana_types[land][constants.DATA_FIELD_COUNT] / total_count) * number_of_lands))

            land_count = min(land_count, total_lands)
            total_lands -= land_count

            if land_count:
                card = {constants.DATA_FIELD_COLORS: mana_types[land]["color"],
                        constants.DATA_FIELD_TYPES: constants.CARD_TYPE_LAND,
                        constants.DATA_FIELD_CMC: 0,
                        constants.DATA_FIELD_NAME: land,
                        constants.DATA_FIELD_MANA_COST: mana_types[land]["color"],
                        constants.DATA_FIELD_COUNT: land_count}
                combined_deck.append(card)

    except Exception as error:
        logger.error(error)
    return combined_deck


def suggest_deck(taken_cards, metrics, configuration):
    """The function will analyze the list of taken cards and produce several viable decks based on specific criteria"""
    colors_max = 5
    maximum_card_count = 22
    sorted_decks = {}
    try:
        deck_types = {"Mid": configuration.card_logic.deck_mid,
                      "Aggro": configuration.card_logic.deck_aggro,
                      "Control": configuration.card_logic.deck_control}
        # Identify the top color combinations
        colors = deck_colors(taken_cards, colors_max, metrics, configuration)
        filtered_colors = []

        colors.pop(constants.FILTER_OPTION_ALL_DECKS, None)

        # Collect color stats and remove colors that don't meet the minimum requirements
        for color in colors:
            creature_count, noncreature_count = deck_color_stats(
                taken_cards, color)
            if ((creature_count >= configuration.card_logic.minimum_creatures) and
               (noncreature_count >= configuration.card_logic.minimum_noncreatures) and
               (creature_count + noncreature_count >= maximum_card_count)):
                filtered_colors.append(color)

        decks = {}
        threshold = metrics.mean - 0.33 * metrics.standard_deviation
        for color in filtered_colors:
            for key, value in deck_types.items():
                deck, sideboard_cards = build_deck(
                    value, taken_cards, color, metrics, configuration)
                rating = deck_rating(
                    deck, value, color, threshold, configuration.settings.bayesian_average_enabled)
                if rating >= configuration.card_logic.ratings_threshold:

                    if ((color not in decks) or
                            (color in decks and rating > decks[color]["rating"])):
                        decks[color] = {}
                        decks[color]["deck_cards"] = stack_cards(deck)
                        decks[color]["sideboard_cards"] = stack_cards(
                            sideboard_cards)
                        decks[color]["rating"] = rating
                        decks[color]["type"] = key
                        decks[color]["deck_cards"].extend(mana_base(deck))

        sorted_colors = sorted(
            decks, key=lambda x: decks[x]["rating"], reverse=True)
        for color in sorted_colors:
            sorted_decks[color] = decks[color]
    except Exception as error:
        logger.error(error)

    return sorted_decks


def build_deck(deck_type, cards, color, metrics, configuration):
    """The function will build a deck list that meets specific criteria"""
    minimum_distribution = deck_type.distribution
    maximum_card_count = deck_type.maximum_card_count
    maximum_deck_size = 40
    cmc_average = deck_type.cmc_average
    recommended_creature_count = deck_type.recommended_creature_count
    deck_list = []
    unused_creature_list = []
    sideboard_list = cards[:]  # Copy by value
    try:
        for card in cards:
            card["results"] = [calculate_win_rate(card[constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIHWR],
                                                  card[constants.DATA_FIELD_DECK_COLORS][color][constants.DATA_FIELD_GIH],
                                                  configuration.settings.bayesian_average_enabled)]

        # identify a splashable color
        splash_threshold = metrics.mean + \
            2.33 * metrics.standard_deviation
        color += (color_splash(cards, color, splash_threshold, configuration))

        card_colors_sorted = deck_card_search(
            cards, color, [constants.CARD_TYPE_CREATURE], True, True, False)
        card_colors_sorted = sorted(
            card_colors_sorted, key=lambda k: k["results"][0], reverse=True)

        # Identify creatures that fit distribution
        distribution = [0, 0, 0, 0, 0, 0, 0]
        used_count = 0
        used_cmc_combined = 0
        for card in card_colors_sorted:
            index = int(min(card[constants.DATA_FIELD_CMC],
                        len(minimum_distribution) - 1))
            if distribution[index] < minimum_distribution[index]:
                deck_list.append(card)
                sideboard_list.remove(card)
                distribution[index] += 1
                used_count += 1
                used_cmc_combined += card[constants.DATA_FIELD_CMC]
            else:
                unused_creature_list.append(card)

        # Go back and identify remaining creatures that have the highest base rating but don't push average above the threshold
        unused_cmc_combined = cmc_average * recommended_creature_count - used_cmc_combined

        unused_creature_list.sort(key=lambda x: x["results"][0], reverse=True)

        # Identify remaining cards that won't exceed recommeneded CMC average
        cmc_cards, unused_creature_list = card_cmc_search(
            unused_creature_list, 0, 0, unused_cmc_combined, recommended_creature_count - used_count)

        for card in cmc_cards:
            deck_list.append(card)
            sideboard_list.remove(card)

        total_card_count = len(deck_list)

        if len(cmc_cards) == 0:
            for card in unused_creature_list:
                if total_card_count >= recommended_creature_count:
                    break

                deck_list.append(card)
                sideboard_list.remove(card)
                total_card_count += 1

        card_colors_sorted = deck_card_search(sideboard_list, color, [
            constants.CARD_TYPE_CREATURE,
            constants.CARD_TYPE_INSTANT,
            constants.CARD_TYPE_SORCERY,
            constants.CARD_TYPE_ENCHANTMENT,
            constants.CARD_TYPE_ARTIFACT,
            constants.CARD_TYPE_PLANESWALKER], True, True, False)

        card_colors_sorted = sorted(
            card_colors_sorted, key=lambda k: k["results"][0], reverse=True)

        # Add remaining non-land cards
        for card in card_colors_sorted:
            if total_card_count >= maximum_card_count:
                break

            deck_list.append(card)
            sideboard_list.remove(card)
            total_card_count += 1

        # Add in special lands if they have a win rate that is at least 0.33 standard deviations from the mean (C-)
        land_cards = deck_card_search(
            sideboard_list, color, [constants.CARD_TYPE_LAND], True, True, False)
        land_cards = [
            x for x in land_cards if x[constants.DATA_FIELD_NAME] not in constants.BASIC_LANDS]
        land_cards = sorted(
            land_cards, key=lambda k: k["results"][0], reverse=True)
        for card in land_cards:
            if total_card_count >= maximum_deck_size:
                break

            if card["results"][0] >= metrics.mean - 0.33 * metrics.standard_deviation:
                deck_list.append(card)
                sideboard_list.remove(card)
                total_card_count += 1

    except Exception as error:
        logger.error(error)
    return deck_list, sideboard_list
