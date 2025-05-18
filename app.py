
import streamlit as st
import random
import json
from treys import Card, Evaluator, Deck

st.set_page_config(page_title="PLO Simulator", layout="wide")
st.title("Pot Limit Omaha Simulator")

ranks = "23456789TJQKA"
suits = "shdc"
all_cards = [r + s for r in ranks for s in suits]

def card_selector(label, used_cards):
    options = [""] + [c for c in all_cards if c not in used_cards]
    return st.selectbox(label, options)

def select_hand(player_label, used_cards):
    st.subheader(player_label)
    cols = st.columns(4)
    hand = []
    for i in range(4):
        with cols[i]:
            c = card_selector(f"{player_label} kort {i+1}", used_cards)
            if c:
                hand.append(c)
                used_cards.add(c)
    return hand

def select_board(used_cards):
    st.subheader("Board kort")
    cols = st.columns(5)
    board = []
    for i in range(5):
        with cols[i]:
            c = card_selector(["Flop 1", "Flop 2", "Flop 3", "Turn", "River"][i], used_cards)
            if c:
                board.append(c)
                used_cards.add(c)
    return board

def save_hand(hero, opponents, board):
    hand_data = {"hero": hero, "opponents": opponents, "board": board}
    with open("saved_hand.json", "w") as f:
        json.dump(hand_data, f)
    st.success("Hånd gemt som saved_hand.json")

def load_hand():
    try:
        with open("saved_hand.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Ingen gemt hånd fundet.")
        return None

def simulate(hero, opponents, board, street, num_simulations):
    evaluator = Evaluator()
    wins = [0] * len(opponents)
    ties = 0
    hero_wins = 0

    known = hero + [c for o in opponents for c in o] + board
    remaining = [Card.new(c) for c in all_cards if c not in known]

    for _ in range(num_simulations):
        deck = Deck()
        for c in known:
            if c in deck.cards:
                deck.cards.remove(Card.new(c))

        full_board = board + [Card.int_to_str(c) for c in deck.draw(5 - len(board))]
        street_index = {"Preflop": 0, "Flop": 3, "Turn": 4, "River": 5}[street]
        sim_board = [Card.new(c) for c in full_board[:street_index]]

        hero_hand = [Card.new(c) for c in hero]
        hero_score = evaluator.evaluate(hero_hand, sim_board)
        hero_best = True
        tie = False

        for i, opp in enumerate(opponents):
            opp_hand = [Card.new(c) for c in opp]
            opp_score = evaluator.evaluate(opp_hand, sim_board)
            if opp_score < hero_score:
                hero_best = False
            elif opp_score == hero_score:
                tie = True

        if hero_best and not tie:
            hero_wins += 1
        elif tie:
            ties += 1

    st.subheader("Resultat")
    st.write(f"Hero vinder: {hero_wins} / {num_simulations} ({hero_wins/num_simulations:.2%})")
    st.write(f"Tie: {ties} / {num_simulations} ({ties/num_simulations:.2%})")

# Brugerflade
used_cards = set()
hero_hand = select_hand("Hero", used_cards)

num_opponents = st.slider("Antal modstandere", 1, 3, 2)
opponent_hands = []
for i in range(num_opponents):
    st.markdown("---")
    if st.checkbox(f"Vælg hånd manuelt for Modstander {i+1}", value=False):
        opponent_hands.append(select_hand(f"Modstander {i+1}", used_cards))
    else:
        random_hand = []
        while len(random_hand) < 4:
            c = random.choice(all_cards)
            if c not in used_cards:
                random_hand.append(c)
                used_cards.add(c)
        opponent_hands.append(random_hand)

st.markdown("---")
board_cards = select_board(used_cards)

street = st.selectbox("Vælg street til simulering", ["Preflop", "Flop", "Turn", "River"])
num_simulations = st.slider("Antal simuleringer", 1, 20000, 1000, step=100)

if st.button("Kør simulering"):
    simulate(hero_hand, opponent_hands, board_cards, street, num_simulations)

st.markdown("---")
if st.button("Gem hånd"):
    save_hand(hero_hand, opponent_hands, board_cards)

if st.button("Indlæs hånd"):
    loaded = load_hand()
    if loaded:
        st.json(loaded)
