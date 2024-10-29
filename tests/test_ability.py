import pytest
from boss_battles.ability import AbilityRegistry, Punch, CureWounds, Longsword, FireBolt, Cower
from boss_battles.character import Stats, Boss, Player


def test_basic_attack_verification():
    punch = Punch()
    
    # Test the verify method of Punch
    # It is an ability that is always successful
    assert punch.verify("abcd", "ac") == True
    assert punch.verify("abc", "ac") == True
    assert punch.verify("abcd", "xx") == True

def test_cure_algorithm():
    cure = CureWounds()
    
    # Test the algorithm method of Heal
    result = cure.algorithm("abcd")
    assert result == "abcd", "Heal algorithm failed"

def test_heal_verification():
    cure = CureWounds()
    
    # Test the verify method of Heal
    assert cure.verify("abcde", "abcde") == True, "Heal verify failed with correct solve_token"
    assert cure.verify("abcd", "xx") == False, "Heal verify failed with incorrect solve_token"

def test_registry_contains_abilities():
    # Test that abilities have been correctly registered in the AbilityRegistry
    assert "punch" in AbilityRegistry.registry, "BasicAttack was not registered in the AbilityRegistry"
    assert "cure" in AbilityRegistry.registry, "Heal was not registered in the AbilityRegistry"
    
    # Test that registered classes are correct
    assert AbilityRegistry.registry["punch"] == Punch, "Punch registration failed"
    assert AbilityRegistry.registry["cure"] == CureWounds, "Cure Wounds registration failed"

def test_registry_lookup():
    # Test the registry lookup and instantiation of abilities
    ability_class = AbilityRegistry.registry.get("punch")
    assert ability_class is Punch, "Registry lookup for BasicAttack failed"
    
    # Instantiate and use the ability
    ability_instance = ability_class()
    assert ability_instance.verify("doesnt", "matter") == True, "Registry lookup for Punch instantiation failed"
    
    ability_class = AbilityRegistry.registry.get("cure")
    assert ability_class is CureWounds, "Registry lookup for Cure Wounds failed"
    
    # Instantiate and use the ability
    ability_instance = ability_class()
    assert ability_instance.verify("dcba", "dcba") == True


def test_swift_longsword_registry_lookup():
    lsword = AbilityRegistry.registry.get("lsword")
    assert lsword is Longsword


def test_swift_longsword_algorithm():
    lsword = Longsword()
    assert lsword.algorithm(op_token="abcd") == "abcd"


