
import streamlit as st
import random
import json
from treys import Card, Evaluator, Deck

st.set_page_config(page_title="PLO Simulator", layout="wide")
st.title("Pot Limit Omaha Simulator")

# Funktion til kortvælger
def card_selector(label):
    ranks = "23456789TJQKA"
    suits = "shdc"
    cards = [r + s for r in ranks for s in suits]
    return st.selectbox(label, [""] + cards)

# Funktion til at oprette hånd
def select_hand(player_label):
    st.subheader(player_label)
    cols = st.columns(4)
    return [card_selector(f"{player_label} kort {i+1}") for i, col in enumerate(cols)]

# Gem hænder til fil
def save_hand(hero, opponents, board):
    hand_data = {"hero": hero, "opponents": opponents, "board": board}
    with open("/mnt/data/saved_hand.json", "w") as f:
        json.dump(hand_data, f)
    st.success("Hånd gemt som saved_hand.json")

# Load hånd
def load_hand():
    try:
        with open("/mnt/data/saved_hand.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Ingen gemt hånd fundet.")
        return None

# Hero håndvalg
hero_hand = select_hand("Hero")

# Antal modstandere
num_opponents = st.slider("Antal modstandere", 1, 3, 2)
opponent_hands = []
for i in range(num_opponents):
    if st.checkbox(f"Vælg hånd manuelt for Modstander {i+1}", value=False):
        opponent_hands.append(select_hand(f"Modstander {i+1}"))
    else:
        opponent_hands.append(random.sample([r + s for r in "23456789TJQKA" for s in "shdc" if r + s not in hero_hand], 4))

# Board kortvalg
st.subheader("Board kort")
board = [card_selector("Flop 1"), card_selector("Flop 2"), card_selector("Flop 3"),
         card_selector("Turn"), card_selector("River")]

# Gem hånd
if st.button("Gem hånd"):
    save_hand(hero_hand, opponent_hands, board)

# Load hånd
if st.button("Indlæs gemt hånd"):
    loaded = load_hand()
    if loaded:
        st.json(loaded)
