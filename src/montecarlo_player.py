from game.players import BasePokerPlayer
from game.engine.card import Card
from game.engine.hand_evaluator import HandEvaluator
import random

class MonteCarloPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        # 勝率模擬
        win_rate = self.estimate_hole_card_win_rate(
            nb_simulation=500,
            nb_player=len(round_state['seats']),
            hole_card=hole_card,
            community_card=round_state["community_card"]
        )
        print(f"Estimated Win Rate: {win_rate:.2f}")
        call_cost = round_state['call_amount']
        pot = round_state['pot']

        if call_cost == 0:
            pot_odds = 0.0001
        else:
            pot_odds = call_cost / (pot + call_cost)

        RR = win_rate / pot_odds

        # 合法下注上下限
        min_raise = valid_actions[2]["amount"]["min"]
        max_raise = valid_actions[2]["amount"]["max"]

        # 定義下注離散化集合
        raise_sizes = [
            int(pot * 0.25),
            int(pot * 0.5),
            int(pot * 0.75),
            int(pot),          # pot-size bet
            max_raise          # all-in 通常等於 player stack
        ]

        # 篩選合法的 raise amount（避免超出合法範圍）
        legal_raise_sizes = [amt for amt in raise_sizes if min_raise <= amt <= max_raise]

        print(f"RR: {RR:.2f}, Win Rate: {win_rate:.2f}, Pot Odds: {pot_odds:.2f}, Call Cost: {call_cost}, Pot: {pot}")
        # 決策邏輯
        if RR < 0.8:
            action = valid_actions[0]  # fold
            amount = action["amount"]
        elif 0.8 <= RR < 1.0:
            if random.random() < 0.15 and legal_raise_sizes:
                action = valid_actions[2]  # bluff raise
                amount = legal_raise_sizes[0]  # 使用最小的 raise（例如0.25 pot）
            else:
                action = valid_actions[0]  # fold
                amount = action["amount"]
        elif 1.0 <= RR < 1.3:
            if random.random() < 0.4 and legal_raise_sizes:
                action = valid_actions[2]
                amount = legal_raise_sizes[len(legal_raise_sizes)//2]  # 選中間金額
            else:
                action = valid_actions[1]  # call
                amount = action["amount"]
        else:
            if random.random() < 0.7 and legal_raise_sizes:
                action = valid_actions[2]
                amount = legal_raise_sizes[-1]  # 選最大的合法 raise（max 或 all-in）
            else:
                action = valid_actions[1]
                amount = action["amount"]

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
