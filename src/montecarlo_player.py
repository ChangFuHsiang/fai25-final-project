from game.players import BasePokerPlayer
from game.engine.card import Card
from game.engine.hand_evaluator import HandEvaluator
import random

class MonteCarloPlayer(BasePokerPlayer):
    def __init__(self):
        self.uuid = None
        self.stack = 1000  # 預設起始籌碼
        self.throw = 0     # 每局投入籌碼

    def declare_action(self, valid_actions, hole_card, round_state):
        nb_player = len(round_state['seats'])
        community_card = round_state['community_card']
        win_rate = self.estimate_hole_card_win_rate(300, nb_player, hole_card, community_card)
        print(f"[DEBUG] Estimated Win Rate: {win_rate:.2f}")

        pot = round_state['pot']['main']['amount'] + sum(p['amount'] for p in round_state['pot']['side'])
        my_stack = [s for s in round_state['seats'] if s['uuid'] == self.uuid][0]['stack']
        action_history = round_state['action_histories'][round_state['street']]

        max_paid = max((a['paid'] for a in action_history if 'paid' in a), default=0)
        my_paid = next((a['paid'] for a in action_history if a.get('uuid') == self.uuid and 'paid' in a), 0)
        call_cost = max_paid - my_paid
        min_raise = valid_actions[2]['amount']['min'] if len(valid_actions) > 2 else 0

        pot_odds = call_cost / (pot + call_cost) if call_cost > 0 else 0.0001
        rr = win_rate / pot_odds

        self.throw += call_cost
        risk_ratio = call_cost / (my_stack + call_cost)  # 計算本次行動佔現有籌碼比例

        print(f"[DEBUG] Win Rate: {win_rate:.2f}, Call Cost: {call_cost}, Pot: {pot}, RR: {rr:.2f}, Risk Ratio: {risk_ratio:.2f}")

        # 新增：若這次行動要投入超過 30% 籌碼，則需勝率 >= 0.7 才考慮行動
        if risk_ratio > 0.3 and win_rate < 0.7:
            return 'fold', 0

        if win_rate >= 0.8:
            return 'raise', min(3 * min_raise, my_stack)
        elif win_rate >= 0.6:
            return 'raise', min(2 * min_raise, my_stack)
        elif win_rate >= 0.5:
            return ('call', call_cost) if call_cost <= 80 else ('fold', 0)
        elif win_rate >= 0.4:
            return ('call', call_cost) if call_cost <= 40 else ('fold', 0)
        else:
            return ('call', 0) if call_cost == 0 else ('fold', 0)

    def estimate_hole_card_win_rate(self, nb_simulation, nb_player, hole_card, community_card=None):
        print(f"[DEBUG] Estimating win rate for hole card: {hole_card}, community card: {community_card}, simulations: {nb_simulation}")
        if community_card is None:
            community_card = []
        win_count = 0
        community_card = self.gen_cards(community_card)
        # print(f"[DEBUG] Community cards after conversion: {community_card}")
        win_count = sum([
            self._montecarlo_simulation(nb_player, hole_card, community_card)
            for _ in range(nb_simulation)
        ])
        print(f"[DEBUG] Total wins in simulations: {win_count} out of {nb_simulation}")
        return 1.0 * win_count / nb_simulation
    
    def _montecarlo_simulation(self, nb_player, hole_card, community_card):
        print(f"[DEBUG] Running simulation for {nb_player} players with hole card: {hole_card} and community card: {community_card}")
        full_community = self._fill_community_card(community_card, hole_card + community_card)
        print(f"[DEBUG] Full community cards after filling: {full_community}")
        unused_cards = self._pick_unused_card((nb_player - 1) * 2, hole_card + full_community)
        print(f"[DEBUG] Unused cards picked: {unused_cards}")
        opponents_hole = [unused_cards[2*i:2*i+2] for i in range(nb_player - 1)]
        print(f"[DEBUG] Opponents' hole cards: {opponents_hole}")

        my_score = HandEvaluator.eval_hand(hole_card, full_community)
        oppo_scores = [HandEvaluator.eval_hand(h, full_community) for h in opponents_hole]
        print(f"[DEBUG] My score: {my_score}, Opponent scores: {oppo_scores}")
        return 1 if my_score >= max(oppo_scores) else 0
    
    def _fill_community_card(self, base_cards, used_cards):
        need_num = 5 - len(base_cards)
        print(f"[DEBUG] Filling community cards. Base cards: {base_cards}, Need: {need_num} more cards.")
        return base_cards + self._pick_unused_card(need_num, used_cards)

    def _pick_unused_card(self, num, used_cards):
        print(f"[DEBUG] Picking {num} unused cards from used cards: {used_cards}")
        used_ids = [i.to_id() for i in used_cards]
        print(f"[DEBUG] Used card IDs: {used_ids}")
        available_ids = [i for i in range(1, 53) if i not in used_ids]
        chosen = random.sample(available_ids, num)
        print(f"[DEBUG] Picking {num} unused cards. Used IDs: {used_ids}, Available IDs: {available_ids}, Chosen IDs: {chosen}")
        return [Card.from_id(cid) for cid in chosen]
    
    def gen_cards(self, card_strs):
        return [Card.from_str(s) for s in card_strs]    

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.throw = 0

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, new_action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return MonteCarloPlayer()
