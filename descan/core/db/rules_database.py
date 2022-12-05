from typing import Dict

from descan.core.rules.rule import Rule


class RulesDatabase:

    def __init__(self) -> None:
        self.rules: Dict[str, Rule] = {}

    def add_rule(self, rule: Rule) -> None:
        self.rules[rule.get_name()] = rule

    def get_rule(self, rule_name):
        return self.rules[rule_name] if rule_name in self.rules else None

    def get_all_rules(self):
        return self.rules.values()
