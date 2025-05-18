import streamlit as st
import random
from treys import Card, Deck, Evaluator
from itertools import combinations
from collections import Counter
import pandas as pd
import altair as alt

st.set_page_config(page_title="Pot Limit Omaha Simulator", layout="wide")

evaluator = Evaluator()

def parse_hand(text):
    try:
        cards = text.split(",")
        return [Card.new(c.strip()) for c in cards if c.strip()]
    except Exception:
        return []

def hand_to_str(hand):
    return ", ".join(Card.int_to_pretty_str(c) for c in hand)

def simulate(hero_hand, num_players=4, iterations=10000):
    win_counts = [0] * num_players
    tie_counts = [0] * num_players
    hand_types = [Counter() for _ in range(num_players)]

    for _ in range(iterations):
        deck = Deck()
        players = []

        # Hero hand
        if hero_hand:
            players.append(hero_hand)
            for c in hero_hand:
                deck.cards.remove(c)
        else:
            hand = deck.draw(4)
            players.append(hand)

        # Other players
        for _ in range(1, num_players):
            while True:
                hand = deck.draw(4)
                if all(c not in sum(players, []) for c in hand):
                    players.append(hand)
                    break

        board = deck.draw(5)
        scores = []
        for p_hand in players:
            best_score = float("inf")
            best_type = None
            for hand_cards in combinations(p_hand, 2):
                for board_cards in combinations(board, 3):
                    score = evaluator.evaluate(list(board_cards), list(hand_cards))
                    if score < best_score:
                        best_score = score
                        best_type = evaluator.class_to_string(evaluator.get_rank_class(score))
            scores.append((best_score, best_type))

        min_score = min(s[0] for s in scores)
        winners = [i for i, s in enumerate(scores) if s[0] == min_score]

        for i in winners:
            hand_types[i][scores[i][1]] += 1

        if len(winners) == 1:
            win_counts[winners[0]] += 1
        else:
            for i in winners:
                tie_counts[i] += 1

    return win_counts, tie_counts, hand_types

# Streamlit UI
st.title("🃏 Pot Limit Omaha Simulator")

num_players = st.slider("Antal spillere", 2, 8, 4)

hero_input = st.text_input("Hero's hånd (f.eks. As,Kd,Qc,Jh)", value="")
hero_hand = parse_hand(hero_input) if hero_input else None
show_raw_cards = st.checkbox("Vis kort med emojis", value=True)

if st.button("Start simulering (10.000 hænder)"):
    with st.spinner("Simulerer..."):
        wins, ties, types = simulate(hero_hand, num_players, 10000)

    st.success("✅ Simulering færdig")

    df = pd.DataFrame({
        "Spiller": [f"Hero" if i == 0 else f"Spiller {i+1}" for i in range(num_players)],
        "Sejre": wins,
        "Delte Pots": ties,
        "Sejr %": [round(w / 10000 * 100, 2) for w in wins]
    })

    st.subheader("📊 Resultater")
    st.dataframe(df)

    chart = alt.Chart(df).mark_bar().encode(
        x="Spiller", y="Sejr %", color="Spiller"
    ).properties(title="Sejr % pr. spiller")
    st.altair_chart(chart, use_container_width=True)

    st.subheader("🏆 Håndtyper")
    for i in range(num_players):
        if types[i]:
            st.markdown(f"**{'Hero' if i == 0 else f'Spiller {i+1}'}**")
            st.write(dict(types[i]))
