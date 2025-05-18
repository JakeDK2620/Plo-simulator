
import streamlit as st
import random
import json
from treys import Card, Deck, Evaluator

# --- Funktioner ---
def generate_random_hand(existing_cards):
    deck = Deck()
    hand = []
    while len(hand) < 4:
        card = deck.draw(1)[0]
        if card not in existing_cards:
            hand.append(card)
            existing_cards.add(card)
    return hand

def convert_card_to_str(card):
    return Card.int_to_pretty_str(card)

def parse_manual_cards(input_cards, existing_cards):
    hand = []
    for c in input_cards:
        if c != 'None':
            try:
                card_int = Card.new(c)
                if card_int in existing_cards:
                    raise ValueError(f"Card {c} already used")
                hand.append(card_int)
                existing_cards.add(card_int)
            except Exception as e:
                st.error(f"Invalid card input: {c}")
    return hand

def simulate(hero_hand, opponent_hands, board_cards, street, num_simulations):
    evaluator = Evaluator()
    hero_wins = 0
    ties = 0
    total = 0

    for _ in range(num_simulations):
        deck = Deck()
        used = set(hero_hand + [card for hand in opponent_hands for card in hand] + board_cards)
        deck.cards = [c for c in deck.cards if c not in used]

        sim_board = list(board_cards)
        if street == "Preflop":
            sim_board += deck.draw(5)
        elif street == "Flop":
            sim_board += deck.draw(2)
        elif street == "Turn":
            sim_board += deck.draw(1)

        hero_score = evaluator.evaluate(hero_hand, sim_board)
        opp_scores = [evaluator.evaluate(opp, sim_board) for opp in opponent_hands]
        all_scores = [hero_score] + opp_scores

        if hero_score == min(all_scores):
            if all_scores.count(hero_score) == 1:
                hero_wins += 1
            else:
                ties += 1
        total += 1

    return hero_wins, ties, total

# --- Streamlit GUI ---
st.set_page_config(layout="wide")
st.title("🂡 Pot Limit Omaha Simulator (4 players)")

st.sidebar.header("Simulator indstillinger")
num_simulations = st.sidebar.slider("Antal simuleringer", 1, 20000, 1000)
street = st.sidebar.selectbox("Simuler til", ["Preflop", "Flop", "Turn", "River"])

st.header("1️⃣ Vælg Hero hånd")
cols = st.columns(4)
hero_input = []
for i in range(4):
    with cols[i]:
        card = st.text_input(f"Kort {i+1} (fx 'As', 'Td')", key=f"hero_card_{i}")
        hero_input.append(card)

st.header("2️⃣ Vælg modstandere")
opponent_hands = []
for opp in range(3):
    st.subheader(f"Modstander {opp+1}")
    use_random = st.checkbox(f"Tilfældig hånd for modstander {opp+1}", value=True, key=f"rand_opp_{opp}")
    if use_random:
        opponent_hands.append("RANDOM")
    else:
        cols = st.columns(4)
        cards = []
        for i in range(4):
            with cols[i]:
                card = st.text_input(f"Kort {i+1}", key=f"opp_{opp}_card_{i}")
                cards.append(card)
        opponent_hands.append(cards)

st.header("3️⃣ Vælg Board kort")
board_cards = []
board_cols = st.columns(5)
for i, label in enumerate(["Flop 1", "Flop 2", "Flop 3", "Turn", "River"]):
    with board_cols[i]:
        card = st.text_input(label, key=f"board_{i}")
        board_cards.append(card)

if st.button("▶️ Kør simulering"):
    existing_cards = set()
    hero = parse_manual_cards(hero_input, existing_cards)

    opponents = []
    for opp in opponent_hands:
        if opp == "RANDOM":
            hand = generate_random_hand(existing_cards)
        else:
            hand = parse_manual_cards(opp, existing_cards)
        opponents.append(hand)

    parsed_board = parse_manual_cards(board_cards, existing_cards)
    st.success("Simulering i gang...")

    wins, ties, total = simulate(hero, opponents, parsed_board, street, num_simulations)
    st.subheader("📊 Resultater")
    st.write(f"Hero vinder: **{wins / total * 100:.2f}%**")
    st.write(f"Hero deler pot: **{ties / total * 100:.2f}%**")

    st.subheader("💾 Gem setup")
    if st.button("Gem som JSON"):
        export_data = {
            "hero": [Card.int_to_str(c) for c in hero],
            "opponents": [[Card.int_to_str(c) for c in h] for h in opponents],
            "board": [Card.int_to_str(c) for c in parsed_board],
            "street": street,
            "simulations": num_simulations
        }
        with open("plo_simulation.json", "w") as f:
            json.dump(export_data, f)
        st.success("Hænder gemt som plo_simulation.json")
