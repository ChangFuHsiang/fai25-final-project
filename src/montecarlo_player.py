from game.players import BasePokerPlayer
from game.engine.card import Card
from game.engine.hand_evaluator import HandEvaluator
import random

class MonteCarloPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        # 勝率模擬
        win_rate = self.estimate_hole_card_win_rate(
            nb_simulation=300,
            nb_player=2,
            hole_card=hole_card,
            community_card=round_state["community_card"]
        )

        # 三段式策略
        if win_rate > 0.85:
            action = valid_actions[2]  # raise
            amount = action["amount"]["max"]
        elif win_rate > 0.7:
            action = valid_actions[2]  # raise
            amount = action["amount"]["min"]
        elif win_rate > 0.4:
            action = valid_actions[1]  # call
            amount = action["amount"]
        else:
            action = valid_actions[0]  # fold
            amount = action["amount"]

        return action["action"], amount

    def estimate_hole_card_win_rate(self, nb_simulation, nb_player, hole_card, community_card=None):
        if community_card is None:
            community_card = []
        hole_card = self.gen_cards(hole_card)
        community_card = self.gen_cards(community_card)
        win_count = sum([
            self._montecarlo_simulation(nb_player, hole_card, community_card)
            for _ in range(nb_simulation)
        ])
        return 1.0 * win_count / nb_simulation

    def _montecarlo_simulation(self, nb_player, hole_card, community_card):
        full_community = self._fill_community_card(community_card, hole_card + community_card)
        unused_cards = self._pick_unused_card((nb_player - 1) * 2, hole_card + full_community)
        opponents_hole = [unused_cards[2*i:2*i+2] for i in range(nb_player - 1)]

        my_score = HandEvaluator.eval_hand(hole_card, full_community)
        oppo_scores = [HandEvaluator.eval_hand(h, full_community) for h in opponents_hole]
        return 1 if my_score >= max(oppo_scores) else 0

    def _fill_community_card(self, base_cards, used_cards):
        need_num = 5 - len(base_cards)
        return base_cards + self._pick_unused_card(need_num, used_cards)

    def _pick_unused_card(self, num, used_cards):
        used_ids = [card.to_id() for card in used_cards]
        available_ids = [i for i in range(1, 53) if i not in used_ids]
        chosen = random.sample(available_ids, num)
        return [Card.from_id(cid) for cid in chosen]

    def gen_cards(self, card_strs):
        return [Card.from_str(s) for s in card_strs]

    # 以下為作業格式要求的 6 個 callback 函式
    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, new_action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

# 作業格式要求：提供 setup_ai() 供系統調用
def setup_ai():
    return MonteCarloPlayer()
