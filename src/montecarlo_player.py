from game.players import BasePokerPlayer
from game.engine.card import Card
from game.engine.hand_evaluator import HandEvaluator
import math
import random

class MonteCarloPlayer(BasePokerPlayer):
    def __init__(self):
        self.uuid = None
        self.stack = 1000  
        self.throw = 0     

    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions  => [fold, call, raise]
        win_rate = self.estimate_hole_card_win_rate(
            nb_simulation=5000,
            nb_player=len(round_state['seats']),
            hole_card=hole_card,
            community_card=round_state["community_card"]
        )
        print(f"[DEBUG] Estimated Win Rate: {win_rate:.2f}")

        # pot = round_state["pot"]["main"]["amount"] + sum(p["amount"] for p in round_state["pot"]["side"])
        round_count = round_state["round_count"]  
        my_stack = [s for s in round_state['seats'] if s['uuid'] == self.uuid][0]['stack']
        call_money = valid_actions[1]["amount"]
        money = valid_actions[2]["amount"]["max"]
        min_raise = valid_actions[2]['amount']['min']

        # 風險比例
        self.throw += call_money
        risk_ratio = max(call_money / (my_stack + call_money), min(3 * min_raise, my_stack) / (my_stack + min(3 * min_raise, my_stack)))


        print(f"[DEBUG] Street: {round_state['street']}, Win Rate: {win_rate:.2f}, Call: {call_money}, Stack: {my_stack}, Risk Ratio: {risk_ratio:.2f}")
        if money - math.ceil((21 - round_count) / 2) * 10 - math.floor((21 - round_count) / 2) * 5 > 1000:
            return valid_actions[0]["action"], valid_actions[0]["amount"]

        # 根據 street 做判斷
        street = round_state['street']
        if street == 'preflop':
            if win_rate >= 0.75:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(2 * min_raise, my_stack)
            elif win_rate >= 0.55:
                return 'call', call_money
            elif win_rate >= 0.5:
                if risk_ratio < 0.2:
                    return 'call', call_money
                else:
                    return 'fold', 0
            elif win_rate >= 0.4:
                if call_money <= 20:
                    return 'call', call_money
                else:
                    return 'fold', 0
            else:
                return 'fold', 0

        elif street == 'flop':
            if win_rate >= 0.9:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', int(0.8 * my_stack) if my_stack > 0 else 0
            elif win_rate >= 0.85:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', int(0.7 * my_stack) if my_stack > 0 else 0
            elif win_rate >= 0.8:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(3 * min_raise, my_stack)
            elif win_rate >= 0.7:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(2 * min_raise, my_stack)
            elif win_rate >= 0.45:
                if call_money <= 10:
                    return 'raise',min(min_raise, my_stack)
                else:
                    return 'call', call_money
            else:
                return 'fold', 0

        elif street == 'turn':
            if call_money > my_stack and win_rate >= 0.6: 
                # 我沒辦法完整 call，但可以 all-in
                return 'call', call_money
            elif win_rate >= 0.8:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', int(0.65 * my_stack) if my_stack > 0 else 0
            elif win_rate >= 0.7:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(4 * min_raise, my_stack)
            elif win_rate >= 0.6:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(3 * min_raise, my_stack)
            elif win_rate >= 0.47:
                if call_money <= 10:
                    return 'raise', min(min_raise, my_stack)
                else:
                    return 'call', call_money
            else:
                return 'fold', 0

        elif street == 'river':
            if call_money > my_stack and win_rate >= 0.6: 
                # 我沒辦法完整 call，但可以 all-in
                return 'call', call_money
            elif win_rate >= 0.8:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', int(0.6 * my_stack) if my_stack > 0 else 0
            elif win_rate >= 0.7:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(5 * min_raise, my_stack)
            elif win_rate >= 0.6:
                if my_stack <= min_raise:
                    return 'call', call_money
                else:
                    return 'raise', min(2 * min_raise, my_stack)
            elif win_rate >= 0.45:
                if call_money <= 10:
                    return 'raise', min(min_raise, my_stack)
                else:
                    return 'call', call_money
            else:
                return 'fold', 0

        return 'fold', 0


        # for act in action_history:
        #     if "paid" in act:
        #         max_paid = max(max_paid, act["paid"])
        #     elif "amount" in act:
        #         max_paid = max(max_paid, act["amount"])
        #     if act["uuid"] == my_uuid:
        #         if "paid" in act:
        #             my_paid += act["paid"]
        #         elif "amount" in act:
        #             my_paid += act["amount"]

        # call_cost = max(0, max_paid - my_paid)

        # print(f"Win Rate: {win_rate:.2f}, Call Cost: {call_cost}, Pot: {pot}")

        # if call_cost == 0:
        #     pot_odds = 0.0001
        # else:
        #     pot_odds = call_cost / (pot + call_cost)

        # RR = win_rate / pot_odds
        # print(f"RR: {RR:.2f} (Win Rate / Pot Odds)")
        # 合法下注上下限
        # min_raise = valid_actions[2]["amount"]["min"]
        # max_raise = valid_actions[2]["amount"]["max"]

        # # 定義下注離散化集合
        # raise_sizes = [
        #     int(pot * 0.25),
        #     int(pot * 0.5),
        #     int(pot * 0.75),
        #     int(pot),          # pot-size bet
        #     max_raise          # all-in 通常等於 player stack
        # ]

        # # 篩選合法的 raise amount（避免超出合法範圍）
        # legal_raise_sizes = [amt for amt in raise_sizes if min_raise <= amt <= max_raise]

        # 檢查 raise 是否可以執行
        # can_raise = (
        #     "raise" in [a['action'] for a in valid_actions]
        #     and isinstance(valid_actions[2]["amount"], dict)
        #     and valid_actions[2]["amount"]["min"] != -1
        #     and valid_actions[2]["amount"]["max"] != -1
        #     and valid_actions[2]["amount"]["min"] <= valid_actions[2]["amount"]["max"]
        # )

        # action_info = valid_actions[0]  # fold
        # action = action_info['action']
        # amount = action_info['amount']

        # if RR < 0.8:
        #     if can_raise and random.random() < 0.15:
        #         action_info = valid_actions[2]  # raise
        #         action = action_info['action']
        #         amount = action_info['amount']['min']
        #     else:
        #         action_info = valid_actions[0]  # fold
        #         action = action_info['action']
        #         amount = action_info['amount']

        # elif 0.8 <= RR < 1.3:
        #     action_info = valid_actions[1]  # call
        #     action = action_info['action']
        #     amount = action_info['amount']

        # elif 1.3 <= RR < 2.0 and can_raise:
        #     if win_rate > 0.6:
        #         action_info = valid_actions[2]  # raise
        #         action = action_info['action']
        #         amount = action_info['amount']['min'] + 20
        #     else:
        #         action_info = valid_actions[1]  # call
        #         action = action_info['action']
        #         amount = action_info['amount']
                
        # else:
        #     if win_rate > 0.8 and can_raise:
        #         action_info = valid_actions[2]  # raise
        #         action = action_info['action']
        #         amount = min(3*action_info['amount']['min'], action_info['amount']['max'])
        #     elif win_rate > 0.7 and can_raise:
        #         action_info = valid_actions[2]  # raise
        #         action = action_info['action']
        #         amount = min(2*action_info['amount']['min'], action_info['amount']['max'])
        #     else:
        #         action_info = valid_actions[1]  # call
        #         action = action_info['action']
        #         amount = action_info['amount']

        # print(f"Action: {action}, Amount: {amount}")
        # return action, amount

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
        # print(f"Used card IDs: {used_ids}")
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
