from game.players import BasePokerPlayer
from game.engine.card import Card
from game.engine.hand_evaluator import HandEvaluator
from game.engine.deck import Deck
import math
import random

class MonteCarloPlayer(BasePokerPlayer):
    def __init__(self):
        self.order = -1  # 0 = first, 1 = second
        self.throw = 0   # Accumulated money put in this round
        self.modify = 0  # Check if order is initialized

    def declare_action(self, valid_actions, hole_card, round_state):
        print(f"[DEBUG] Valid Actions: {valid_actions}")
        cards = [Card.from_str(hole_card[0]), Card.from_str(hole_card[1])]
        community_card = [Card.from_str(c) for c in round_state["community_card"]]
        round_count = round_state["round_count"]
        pot_amount = round_state["pot"]["main"]["amount"]

        money = valid_actions[2]["amount"]["max"]
        min_raise = valid_actions[2]["amount"]["min"]
        call_money = valid_actions[1]["amount"]

        # Determine player order on preflop
        if self.modify == 0:
            last_action = round_state['action_histories']['preflop'][-1]['action']
            if last_action == 'BIGBLIND':
                self.order = 0
            else:
                self.order = 1
            self.modify = 1

        print(f"[DEBUG] Player Order: {self.order}, Round Count: {round_count}")
        # Estimate win rate using Monte Carlo
        win_rate = self.estimate_hole_card_win_rate(
            nb_simulation=300,
            nb_player=len(round_state['seats']),
            hole_card=cards,
            community_card=community_card
        )

        # Preflop strategy using simple score table
        print(f"[PRE-FLOP DEBUG] score: {score}, call_money: {call_money}, pot: {pot_amount}, round_count: {round_count}")
        if len(community_card) == 0:
            score = self.count_score(cards)
            if score >= 25:
                return self.send_action(call_money, min(3 * min_raise, money))
            elif score >= 23:
                return self.send_action(call_money, min(2 * min_raise, money))
            elif score >= 20:
                return "call", call_money
            elif score >= 15:
                return "call", call_money if call_money <= 50 else ("fold", 0)
            else:
                return "fold", 0 if call_money > 10 else ("call", call_money)

        # Postflop strategy using win rate
        self.throw += call_money
        print(f"[DEBUG] win_rate: {win_rate:.2f}, call_money: {call_money}, pot_amount: {round_state['pot']['main']['amount']}, min_raise: {min_raise}, money: {money}")

        if win_rate >= 0.8:
            print("[DEBUG] Decision: Strong Raise (3x)")
            return self.send_action(call_money, min(3 * min_raise, money))
        elif win_rate >= 0.6:
            print("[DEBUG] Decision: Medium Raise (2x)")
            return self.send_action(call_money, min(2 * min_raise, money))
        elif win_rate >= 0.5:
            print(f"[DEBUG] Decision: Conditional Call or Fold (Threshold: 80)")
            return ("call", call_money) if call_money <= 80 else ("fold", 0)
        elif win_rate >= 0.4:
            print(f"[DEBUG] Decision: Conditional Call or Fold (Threshold: 40)")
            return ("call", call_money) if call_money <= 40 else ("fold", 0)
        else:
            print("[DEBUG] Decision: Weak hand → Fold unless free call")
            return ("call", 0) if call_money == 0 else ("fold", 0)


    def send_action(self, call_money, raise_money):
        if raise_money < 0:
            return "call", call_money
        else:
            return "raise", raise_money

    def count_score(self, cards):
        score_ct = [
            [0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13],
            [1, 30, 23, 22, 22, 22, 19, 19, 19, 20, 23, 25, 25, 25],
            [2, 20, 20, 13, 12, 10,  7,  7,  8,  9, 10, 10, 10, 10],
            [3, 18,  0, 20, 13, 12, 10,  7,  8,  9, 10, 10, 10, 10],
            [4, 17,  0,  0, 20, 13, 12, 10,  9,  9, 10, 10, 10, 10],
            [5, 14,  0,  0,  0, 20, 13, 12, 10, 10, 10, 10, 10, 10],
            [6, 10,  0,  0,  0,  0, 20, 15, 11, 10, 10, 10, 10, 10],
            [7, 10,  0,  0,  0,  0,  0, 20, 15, 11, 11, 11, 12, 13],
            [8, 10,  0,  0,  0,  0,  0,  7, 21, 15, 12, 12, 14, 13],
            [9, 10,  0,  0,  0,  0,  0,  7,  8, 23, 20, 20, 15, 15],
            [10, 17,  0,  0,  0,  0,  7,  7,  8, 11, 25, 23, 20, 20],
            [11, 19,  0,  0,  0,  7,  8,  8,  8, 10, 11, 25, 23, 20],
            [12, 24,  0,  0,  6,  7,  8,  8,  8, 10, 11, 11, 25, 23],
            [13, 25,  0,  6,  7,  8,  9,  9,  9, 10, 11, 11, 11, 26]
        ]
        r1 = cards[0].rank if cards[0].rank != 14 else 1
        r2 = cards[1].rank if cards[1].rank != 14 else 1
        small, large = min(r1, r2), max(r1, r2)
        suited = cards[0].suit == cards[1].suit
        return score_ct[small][large] if suited else score_ct[large][small]

    def estimate_hole_card_win_rate(self, nb_simulation, nb_player, hole_card, community_card):
        win_count = 0
        for _ in range(nb_simulation):
            win_count += self._simulate_one(nb_player, hole_card, community_card)
            print(f"[DEBUG] Simulation {_ + 1}/{nb_simulation}: Current Win Count: {win_count}")
        return win_count / nb_simulation

    def _simulate_one(self, nb_player, hole_card, community_card):
        deck = Deck()
        used = hole_card + community_card
        for c in used:
            deck.cards.remove(c)
        random.shuffle(deck.cards)

        community_needed = 5 - len(community_card)
        sim_community = community_card + [deck.draw_card() for _ in range(community_needed)]

        opp_holes = [[deck.draw_card(), deck.draw_card()] for _ in range(nb_player - 1)]
        my_score = HandEvaluator.eval_hand(hole_card, sim_community)
        opp_scores = [HandEvaluator.eval_hand(h, sim_community) for h in opp_holes]
        print(f"[DEBUG] My Score: {my_score}, Opponent Scores: {opp_scores}")
        return int(my_score >= max(opp_scores))

    def receive_game_start_message(self, game_info):
        pass
 
    def receive_round_start_message(self, round_count, hole_card, seats):
        self.modify = 0
        self.throw = 0
 
    def receive_street_start_message(self, street, round_state):
        pass
 
    def receive_game_update_message(self, new_action, round_state):
        pass
 
    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return MonteCarloPlayer()
