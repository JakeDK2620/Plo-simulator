
import streamlit as st
import random
import json
from itertools import combinations
from collections import Counter
from treys import Card, Evaluator
import matplotlib.pyplot as plt

evaluator = Evaluator()
suits = ['s', 'h', 'd', 'c']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
deck = [r + s for r in ranks for s in suits]

def hand_label(rank_class):
    return evaluator.class_to_string(rank_class)

def to_treys(cards):
    return [Card.new(c) for c in cards]

def plo_best_hand(hand, board):
    best = 7463
    best_class = None
    for h in combinations(hand, 2):
        for b in combinations(board, 3):
            score = evaluator.evaluate(list(h), list(b))
            if score < best:
                best = score
                best_class = evaluator.get_rank_class(score)
    return best, best_class

def get_random_hand(exclude):
    available = list(set(deck) - set(exclude))
    return random.sample(available, 4)

def get_random_board(exclude, n):
    available = list(set(deck) - set(exclude))
    return random.sample(available, n)

def simulate(hero_hand, opponent_hands, board_cards, street, num_sims, randomize_opps):
    wins = ties = 0
    hero_stats = Counter()
    all_stats = Counter()
    hero_treys = to_treys(hero_hand)
    board_base = to_treys(board_cards)
    needed = {'preflop': 5, 'flop': 2, 'turn': 1, 'river': 0}[street]

    for _ in range(num_sims):
        used = set(hero_hand + board_cards)
        sim_board_str = board_cards + get_random_board(used, needed)
        sim_board = to_treys(sim_board_str)
        used.update(sim_board_str)

        current_opps = []
        for opp in opponent_hands:
            if randomize_opps or len(opp) != 4:
                hand = get_random_hand(used)
                used.update(hand)
                current_opps.append(to_treys(hand))
            else:
                current_opps.append(to_treys(opp))

        h_score, h_class = plo_best_hand(hero_treys, sim_board)
        hero_stats[h_class] += 1
        all_stats[h_class] += 1
        opp_scores = []
        for opp in current_opps:
            o_score, o_class = plo_best_hand(opp, sim_board)
            opp_scores.append((o_score, o_class))
            all_stats[o_class] += 1

        opp_values = [s[0] for s in opp_scores]
        if all(h_score < s for s in opp_values):
            wins += 1
        elif any(h_score == s for s in opp_values):
            ties += 1

    return wins, ties, num_sims, hero_stats, all_stats

# Streamlit UI
st.title("PLO Simulator – 2 til 8 spillere med statistik og eksport")

num_players = st.slider("Antal spillere (inkl. Hero)", 2, 8, 4)
num_opponents = num_players - 1

hero_hand = st.multiselect("Vælg Hero's hånd (4 kort)", options=deck, max_selections=4)

board_choices = list(set(deck) - set(hero_hand))
board = st.multiselect("Vælg Board-kort (op til 5)", options=sorted(board_choices), max_selections=5)

opponent_hands = []
randomize_opps = st.checkbox("Brug tilfældige hænder for modstandere", value=True)
for i in range(num_opponents):
    if not randomize_opps:
        opp = st.multiselect(f"Modstander {i+1} hånd (4 kort)", options=deck, max_selections=4, key=f"opp_{i}")
    else:
        opp = []
    opponent_hands.append(opp)

street = st.selectbox("Street", ["preflop", "flop", "turn", "river"])
num_sims = st.slider("Antal simuleringer", 100, 20000, 1000)

if street == "preflop" and len(board) > 0:
    st.error("Du må ikke vælge boardkort ved preflop-simulering.")
elif street == "river" and len(board) < 5:
    st.error("River-simulering kræver præcis 5 boardkort.")
elif st.button("Kør simulering"):
    if len(hero_hand) != 4:
        st.error("Hero skal have præcis 4 kort.")
    elif not randomize_opps and any(len(opp) != 4 for opp in opponent_hands):
        st.error("Alle modstandere skal have 4 kort.")
    else:
        wins, ties, total, hero_stats, all_stats = simulate(hero_hand, opponent_hands, board, street, num_sims, randomize_opps)

        st.success(f"Hero vinder: {wins}/{total} = {wins/total:.2%}")
        st.info(f"Split pot: {ties}/{total} = {ties/total:.2%}")
        st.warning(f"Hero taber: {(total - wins - ties)}/{total} = {(total - wins - ties)/total:.2%}")

        st.subheader("Håndtyper i Hero's hænder")
        st.json({hand_label(k): v for k, v in hero_stats.items()})

        st.subheader("Håndtyper i alle hænder")
        st.json({hand_label(k): v for k, v in all_stats.items()})

        # Grafer
        def show_bar(stats, title):
            if not stats: return
            labels = [hand_label(k) for k in stats.keys()]
            values = list(stats.values())
            fig, ax = plt.subplots()
            ax.bar(labels, values)
            plt.xticks(rotation=45)
            ax.set_title(title)
            st.pyplot(fig)

        show_bar(hero_stats, "Hero's håndtyper")
        show_bar(all_stats, "Alle håndtyper")

        # Eksport
        result_data = {
            "hero_hand": hero_hand,
            "board": board,
            "wins": wins,
            "ties": ties,
            "total": total,
            "hero_stats": {hand_label(k): v for k, v in hero_stats.items()},
            "all_stats": {hand_label(k): v for k, v in all_stats.items()}
        }

        st.download_button("Download resultater som JSON", json.dumps(result_data, indent=2), file_name="plo_results.json")
