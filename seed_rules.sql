-- ============================================
-- Seed Rules for MTG Rule Engine
-- ============================================
-- This file contains common MTG rule templates
-- to bootstrap the rule engine
-- ============================================

BEGIN;

-- ============================================
-- RULE CATEGORIES
-- ============================================

INSERT INTO rule_categories (name, description, color, sort_order) VALUES
    -- Core categories
    ('Removal', 'Effects that remove permanents from play', '#DC143C', 100),
    ('Card Draw', 'Effects that draw cards', '#1E90FF', 200),
    ('Mana Production', 'Effects that produce or accelerate mana', '#228B22', 300),
    ('Life Manipulation', 'Effects that gain or lose life', '#FFD700', 400),
    ('Token Generation', 'Effects that create creature tokens', '#9370DB', 500),
    ('Counterspells', 'Effects that counter spells on the stack', '#4169E1', 600),
    ('Tutors', 'Effects that search library for specific cards', '#8B4513', 700),
    ('Graveyard Interaction', 'Effects that interact with graveyard', '#2F4F4F', 800),
    ('Combat Mechanics', 'Effects related to combat and attacking', '#B22222', 900),
    ('Tribal Synergy', 'Effects that benefit specific creature types', '#DAA520', 1000),
    ('Protection', 'Effects that protect permanents or players', '#FFFFFF', 1100),
    ('Card Advantage', 'Effects that generate card advantage', '#00CED1', 1200),
    ('Resource Denial', 'Effects that deny opponents resources', '#696969', 1300),
    ('Combo Enablers', 'Effects that enable infinite combos or loops', '#FF69B4', 1400),
    ('Evasion', 'Effects that help creatures deal combat damage', '#87CEEB', 1500)
ON CONFLICT (name) DO NOTHING;

-- Subcategories (using parent_category_id)
WITH removal_cat AS (SELECT id FROM rule_categories WHERE name = 'Removal'),
     graveyard_cat AS (SELECT id FROM rule_categories WHERE name = 'Graveyard Interaction'),
     combat_cat AS (SELECT id FROM rule_categories WHERE name = 'Combat Mechanics')
INSERT INTO rule_categories (name, description, parent_category_id, sort_order) VALUES
    ('Creature Removal', 'Remove creatures specifically', (SELECT id FROM removal_cat), 110),
    ('Permanent Removal', 'Remove any permanent type', (SELECT id FROM removal_cat), 120),
    ('Board Wipes', 'Mass removal effects', (SELECT id FROM removal_cat), 130),
    ('Exile Effects', 'Effects that exile instead of destroy', (SELECT id FROM removal_cat), 140),
    ('Reanimation', 'Return creatures from graveyard to battlefield', (SELECT id FROM graveyard_cat), 810),
    ('Graveyard Recursion', 'Return cards from graveyard to hand', (SELECT id FROM graveyard_cat), 820),
    ('Self-Mill', 'Put cards from library into graveyard', (SELECT id FROM graveyard_cat), 830),
    ('Combat Tricks', 'Instant-speed combat modifications', (SELECT id FROM combat_cat), 910),
    ('Combat Damage Triggers', 'Abilities that trigger on combat damage', (SELECT id FROM combat_cat), 920)
ON CONFLICT (name) DO NOTHING;


-- ============================================
-- RULES: REMOVAL
-- ============================================

WITH removal_cat AS (SELECT id FROM rule_categories WHERE name = 'Creature Removal'),
     permanent_cat AS (SELECT id FROM rule_categories WHERE name = 'Permanent Removal'),
     board_wipe_cat AS (SELECT id FROM rule_categories WHERE name = 'Board Wipes'),
     exile_cat AS (SELECT id FROM rule_categories WHERE name = 'Exile Effects')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'targeted_creature_destruction',
        'Destroy target creature',
        'destroy\s+target\s+creature',
        (SELECT id FROM removal_cat),
        'Targeted',
        '{"action": "destroy", "target_type": "creature", "targeting": "single"}'::jsonb,
        ARRAY['Destroy target creature.', 'Destroy target creature with flying.', 'Destroy target nonblack creature.'],
        TRUE
    ),
    (
        'targeted_permanent_destruction',
        'Destroy target permanent',
        'destroy\s+target\s+(permanent|artifact|enchantment)',
        (SELECT id FROM permanent_cat),
        'Targeted',
        '{"action": "destroy", "target_type": "permanent", "targeting": "single"}'::jsonb,
        ARRAY['Destroy target artifact or enchantment.', 'Destroy target nonland permanent.'],
        TRUE
    ),
    (
        'board_wipe_creatures',
        'Destroy all creatures',
        'destroy\s+all\s+creatures',
        (SELECT id FROM board_wipe_cat),
        'Mass Removal',
        '{"action": "destroy", "target_type": "creature", "targeting": "all"}'::jsonb,
        ARRAY['Destroy all creatures.', 'Destroy all creatures with power 3 or less.'],
        TRUE
    ),
    (
        'board_wipe_conditional',
        'Destroy all [condition] creatures',
        'destroy\s+all\s+\w+\s+creatures',
        (SELECT id FROM board_wipe_cat),
        'Conditional Mass Removal',
        '{"action": "destroy", "target_type": "creature", "targeting": "conditional", "has_condition": true}'::jsonb,
        ARRAY['Destroy all black creatures.', 'Destroy all creatures with flying.'],
        TRUE
    ),
    (
        'exile_target_creature',
        'Exile target creature',
        'exile\s+target\s+creature',
        (SELECT id FROM exile_cat),
        'Targeted Exile',
        '{"action": "exile", "target_type": "creature", "targeting": "single"}'::jsonb,
        ARRAY['Exile target creature.', 'Exile target creature you don\''t control.'],
        TRUE
    ),
    (
        'exile_permanent',
        'Exile target permanent',
        'exile\s+target\s+\w*\s*permanent',
        (SELECT id FROM exile_cat),
        'Targeted Exile',
        '{"action": "exile", "target_type": "permanent", "targeting": "single"}'::jsonb,
        ARRAY['Exile target nonland permanent.', 'Exile target artifact or enchantment.'],
        TRUE
    ),
    (
        'sacrifice_creature',
        'Target player sacrifices a creature',
        '(target\s+player|opponent)\s+sacrifices?\s+a\s+creature',
        (SELECT id FROM removal_cat),
        'Sacrifice',
        '{"action": "sacrifice", "target_type": "creature", "targets_player": true}'::jsonb,
        ARRAY['Target player sacrifices a creature.', 'Each opponent sacrifices a creature.'],
        TRUE
    ),
    (
        'minus_x_minus_x',
        'Target creature gets -X/-X',
        'target\s+creature\s+gets?\s+-\d+/-\d+',
        (SELECT id FROM removal_cat),
        'Stat Reduction',
        '{"action": "stat_reduction", "target_type": "creature", "stat": "toughness"}'::jsonb,
        ARRAY['Target creature gets -3/-3 until end of turn.', 'Target creature gets -4/-4.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: CARD DRAW
-- ============================================

WITH draw_cat AS (SELECT id FROM rule_categories WHERE name = 'Card Draw'),
     card_adv_cat AS (SELECT id FROM rule_categories WHERE name = 'Card Advantage')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'card_draw_fixed',
        'Draw N cards',
        'draw\s+(?:a\s+card|one|two|three|four|five|\d+\s+cards?)',
        (SELECT id FROM draw_cat),
        'Fixed Draw',
        '{"action": "draw", "quantity_type": "fixed"}'::jsonb,
        ARRAY['Draw a card.', 'Draw two cards.', 'Draw three cards.'],
        TRUE
    ),
    (
        'card_draw_conditional',
        'Draw cards based on condition',
        'draw\s+(?:a\s+card|cards?)\s+(?:for each|equal)',
        (SELECT id FROM draw_cat),
        'Conditional Draw',
        '{"action": "draw", "quantity_type": "conditional", "has_condition": true}'::jsonb,
        ARRAY['Draw a card for each creature you control.', 'Draw cards equal to the number of artifacts you control.'],
        TRUE
    ),
    (
        'card_draw_opponent',
        'Each player draws cards',
        '(?:each player|all players)\s+draws?',
        (SELECT id FROM draw_cat),
        'Group Draw',
        '{"action": "draw", "targets": "all_players"}'::jsonb,
        ARRAY['Each player draws a card.', 'All players draw two cards.'],
        TRUE
    ),
    (
        'scry',
        'Scry N',
        'scry\s+\d+',
        (SELECT id FROM card_adv_cat),
        'Scry',
        '{"action": "scry", "library_manipulation": true}'::jsonb,
        ARRAY['Scry 2.', 'Scry 1, then draw a card.'],
        TRUE
    ),
    (
        'surveil',
        'Surveil N',
        'surveil\s+\d+',
        (SELECT id FROM card_adv_cat),
        'Surveil',
        '{"action": "surveil", "library_manipulation": true, "graveyard_synergy": true}'::jsonb,
        ARRAY['Surveil 2.', 'Surveil 1.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: MANA PRODUCTION
-- ============================================

WITH mana_cat AS (SELECT id FROM rule_categories WHERE name = 'Mana Production')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'tap_for_mana',
        '{T}: Add mana',
        '\{T\}:\s*Add',
        (SELECT id FROM mana_cat),
        'Tap Ability',
        '{"action": "add_mana", "requires_tap": true}'::jsonb,
        ARRAY['{T}: Add {G}.', '{T}: Add one mana of any color.'],
        TRUE
    ),
    (
        'etb_mana',
        'When enters, add mana',
        'when.*enters.*add',
        (SELECT id FROM mana_cat),
        'ETB Mana',
        '{"action": "add_mana", "trigger": "etb", "one_time": true}'::jsonb,
        ARRAY['When this enters, add {G}{G}.'],
        TRUE
    ),
    (
        'ritual_effect',
        'Add multiple mana (Ritual)',
        'add\s+\{[WUBRGC]+\}\{[WUBRGC]+\}',
        (SELECT id FROM mana_cat),
        'Ritual',
        '{"action": "add_mana", "card_type": "instant_sorcery", "temporary": true}'::jsonb,
        ARRAY['Add {R}{R}{R}.', 'Add {G}{G}{G}.', 'Add {B}{B}{B}.'],
        TRUE
    ),
    (
        'mana_dork',
        'Creature that taps for mana',
        '\{T\}:\s*Add.*creature',
        (SELECT id FROM mana_cat),
        'Mana Dork',
        '{"action": "add_mana", "requires_tap": true, "card_type": "creature"}'::jsonb,
        ARRAY['Llanowar Elves', 'Birds of Paradise'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: LIFE MANIPULATION
-- ============================================

WITH life_cat AS (SELECT id FROM rule_categories WHERE name = 'Life Manipulation')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'life_gain_fixed',
        'Gain N life',
        'gain\s+\d+\s+life',
        (SELECT id FROM life_cat),
        'Life Gain',
        '{"action": "gain_life", "quantity_type": "fixed"}'::jsonb,
        ARRAY['Gain 3 life.', 'You gain 5 life.'],
        TRUE
    ),
    (
        'life_gain_conditional',
        'Gain life based on condition',
        'gain.*life.*(?:for each|equal)',
        (SELECT id FROM life_cat),
        'Conditional Life Gain',
        '{"action": "gain_life", "quantity_type": "conditional"}'::jsonb,
        ARRAY['Gain 1 life for each creature you control.'],
        TRUE
    ),
    (
        'life_loss_fixed',
        'Lose N life',
        'lose\s+\d+\s+life',
        (SELECT id FROM life_cat),
        'Life Loss',
        '{"action": "lose_life", "quantity_type": "fixed"}'::jsonb,
        ARRAY['Lose 2 life.', 'Target player loses 3 life.'],
        TRUE
    ),
    (
        'drain_effect',
        'Opponent loses life, you gain life',
        '(?:opponent|target player)\s+loses\s+\d+\s+life.*you\s+gain',
        (SELECT id FROM life_cat),
        'Drain',
        '{"action": "drain", "symmetric": false}'::jsonb,
        ARRAY['Target opponent loses 2 life and you gain 2 life.'],
        TRUE
    ),
    (
        'lifelink_keyword',
        'Has lifelink',
        'lifelink',
        (SELECT id FROM life_cat),
        'Keyword',
        '{"keyword": "lifelink", "combat_related": true}'::jsonb,
        ARRAY['This creature has lifelink.', 'Lifelink'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: DAMAGE
-- ============================================

WITH combat_cat AS (SELECT id FROM rule_categories WHERE name = 'Combat Mechanics')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'direct_damage_fixed',
        'Deal N damage to target',
        'deal\s+\d+\s+damage\s+to',
        (SELECT id FROM combat_cat),
        'Direct Damage',
        '{"action": "deal_damage", "quantity_type": "fixed"}'::jsonb,
        ARRAY['Deal 3 damage to any target.', 'Deal 2 damage to target creature.'],
        TRUE
    ),
    (
        'direct_damage_conditional',
        'Deal damage based on condition',
        'deal.*damage.*(?:for each|equal)',
        (SELECT id FROM combat_cat),
        'Conditional Damage',
        '{"action": "deal_damage", "quantity_type": "conditional"}'::jsonb,
        ARRAY['Deal damage equal to the number of artifacts you control.'],
        TRUE
    ),
    (
        'aoe_damage',
        'Deal damage to multiple targets',
        'deal\s+\d+\s+damage\s+to\s+(?:each|all)',
        (SELECT id FROM combat_cat),
        'AOE Damage',
        '{"action": "deal_damage", "targeting": "multiple"}'::jsonb,
        ARRAY['Deal 1 damage to each creature.', 'Deal 3 damage to each opponent.'],
        TRUE
    ),
    (
        'fight_mechanic',
        'Creatures fight each other',
        'fight',
        (SELECT id FROM combat_cat),
        'Fight',
        '{"action": "fight", "involves_creatures": true}'::jsonb,
        ARRAY['Target creature you control fights target creature you don\''t control.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: TOKEN GENERATION
-- ============================================

WITH token_cat AS (SELECT id FROM rule_categories WHERE name = 'Token Generation')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'create_creature_tokens',
        'Create N creature tokens',
        'create\s+(?:a|one|two|three|\d+)\s+\d+/\d+',
        (SELECT id FROM token_cat),
        'Creature Tokens',
        '{"action": "create_tokens", "token_type": "creature"}'::jsonb,
        ARRAY['Create a 1/1 white Soldier creature token.', 'Create two 2/2 green Bear creature tokens.'],
        TRUE
    ),
    (
        'create_token_copy',
        'Create token copy of creature',
        'create.*token.*copy',
        (SELECT id FROM token_cat),
        'Copy Tokens',
        '{"action": "create_tokens", "token_type": "copy"}'::jsonb,
        ARRAY['Create a token that\''s a copy of target creature.'],
        TRUE
    ),
    (
        'token_on_death',
        'Create token when creature dies',
        'when.*dies.*create',
        (SELECT id FROM token_cat),
        'Death Trigger',
        '{"action": "create_tokens", "trigger": "dies"}'::jsonb,
        ARRAY['When this dies, create a 1/1 black Spirit creature token.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: COUNTERSPELLS
-- ============================================

WITH counter_cat AS (SELECT id FROM rule_categories WHERE name = 'Counterspells')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'counter_spell',
        'Counter target spell',
        'counter\s+target\s+spell',
        (SELECT id FROM counter_cat),
        'Hard Counter',
        '{"action": "counter", "target_type": "spell"}'::jsonb,
        ARRAY['Counter target spell.'],
        TRUE
    ),
    (
        'counter_conditional',
        'Counter target spell unless condition',
        'counter.*unless',
        (SELECT id FROM counter_cat),
        'Soft Counter',
        '{"action": "counter", "target_type": "spell", "has_condition": true}'::jsonb,
        ARRAY['Counter target spell unless its controller pays {3}.'],
        TRUE
    ),
    (
        'counter_creature_spell',
        'Counter target creature spell',
        'counter\s+target\s+creature\s+spell',
        (SELECT id FROM counter_cat),
        'Type-Specific Counter',
        '{"action": "counter", "target_type": "creature_spell"}'::jsonb,
        ARRAY['Counter target creature spell.'],
        TRUE
    ),
    (
        'counter_noncreature_spell',
        'Counter target noncreature spell',
        'counter\s+target\s+noncreature\s+spell',
        (SELECT id FROM counter_cat),
        'Type-Specific Counter',
        '{"action": "counter", "target_type": "noncreature_spell"}'::jsonb,
        ARRAY['Counter target noncreature spell.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: TUTORS
-- ============================================

WITH tutor_cat AS (SELECT id FROM rule_categories WHERE name = 'Tutors')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'tutor_to_hand',
        'Search library for card, put into hand',
        'search.*library.*hand',
        (SELECT id FROM tutor_cat),
        'To Hand',
        '{"action": "tutor", "destination": "hand"}'::jsonb,
        ARRAY['Search your library for a card and put it into your hand.'],
        TRUE
    ),
    (
        'tutor_to_battlefield',
        'Search library for card, put onto battlefield',
        'search.*library.*battlefield',
        (SELECT id FROM tutor_cat),
        'To Battlefield',
        '{"action": "tutor", "destination": "battlefield"}'::jsonb,
        ARRAY['Search your library for a basic land card and put it onto the battlefield.'],
        TRUE
    ),
    (
        'tutor_to_top',
        'Search library for card, put on top',
        'search.*library.*top',
        (SELECT id FROM tutor_cat),
        'To Top of Library',
        '{"action": "tutor", "destination": "top_of_library"}'::jsonb,
        ARRAY['Search your library for a card and put it on top of your library.'],
        TRUE
    ),
    (
        'creature_tutor',
        'Search for creature card',
        'search.*library.*creature',
        (SELECT id FROM tutor_cat),
        'Creature Tutor',
        '{"action": "tutor", "card_type": "creature"}'::jsonb,
        ARRAY['Search your library for a creature card.'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: GRAVEYARD INTERACTION
-- ============================================

WITH graveyard_cat AS (SELECT id FROM rule_categories WHERE name = 'Graveyard Interaction'),
     reanimate_cat AS (SELECT id FROM rule_categories WHERE name = 'Reanimation'),
     recursion_cat AS (SELECT id FROM rule_categories WHERE name = 'Graveyard Recursion'),
     mill_cat AS (SELECT id FROM rule_categories WHERE name = 'Self-Mill')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'reanimate_creature',
        'Return creature from graveyard to battlefield',
        'return.*creature.*graveyard.*battlefield',
        (SELECT id FROM reanimate_cat),
        'Creature Reanimation',
        '{"action": "reanimate", "card_type": "creature", "destination": "battlefield"}'::jsonb,
        ARRAY['Return target creature card from your graveyard to the battlefield.'],
        TRUE
    ),
    (
        'return_to_hand',
        'Return card from graveyard to hand',
        'return.*(?:card|creature).*graveyard.*hand',
        (SELECT id FROM recursion_cat),
        'To Hand',
        '{"action": "recursion", "destination": "hand"}'::jsonb,
        ARRAY['Return target card from your graveyard to your hand.'],
        TRUE
    ),
    (
        'mill_cards',
        'Put cards from library into graveyard',
        'put.*(?:card|cards).*library.*graveyard',
        (SELECT id FROM mill_cat),
        'Mill',
        '{"action": "mill", "self_mill": true}'::jsonb,
        ARRAY['Put the top three cards of your library into your graveyard.'],
        TRUE
    ),
    (
        'flashback_keyword',
        'Has flashback',
        'flashback',
        (SELECT id FROM graveyard_cat),
        'Flashback',
        '{"keyword": "flashback", "graveyard_cast": true}'::jsonb,
        ARRAY['Flashback {3}{R}'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- RULES: EVASION
-- ============================================

WITH evasion_cat AS (SELECT id FROM rule_categories WHERE name = 'Evasion')
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, subcategory, parameters, examples, is_manual) VALUES
    (
        'flying_keyword',
        'Has flying',
        '\bflying\b',
        (SELECT id FROM evasion_cat),
        'Flying',
        '{"keyword": "flying", "evasion_type": "flying"}'::jsonb,
        ARRAY['Flying'],
        TRUE
    ),
    (
        'menace_keyword',
        'Has menace',
        '\bmenace\b',
        (SELECT id FROM evasion_cat),
        'Menace',
        '{"keyword": "menace", "requires_multiple_blockers": true}'::jsonb,
        ARRAY['Menace'],
        TRUE
    ),
    (
        'unblockable',
        'Can''t be blocked',
        'can\''t be blocked',
        (SELECT id FROM evasion_cat),
        'Unblockable',
        '{"evasion_type": "unblockable"}'::jsonb,
        ARRAY['This creature can\''t be blocked.'],
        TRUE
    ),
    (
        'trample_keyword',
        'Has trample',
        '\btrample\b',
        (SELECT id FROM evasion_cat),
        'Trample',
        '{"keyword": "trample", "excess_damage": true}'::jsonb,
        ARRAY['Trample'],
        TRUE
    )
ON CONFLICT (rule_name) DO NOTHING;


-- ============================================
-- KEYWORD ABILITIES (Evergreen)
-- ============================================

INSERT INTO keyword_abilities (keyword, description, rules_text, is_evergreen, is_ability_word, has_parameter, reminder_text) VALUES
    ('flying', 'Can only be blocked by creatures with flying or reach', 'A creature with flying cannot be blocked except by creatures with flying and/or reach.', TRUE, FALSE, FALSE, 'This creature can''t be blocked except by creatures with flying and/or reach.'),
    ('first strike', 'Deals combat damage before normal damage', 'A creature with first strike deals combat damage before creatures without first strike.', TRUE, FALSE, FALSE, 'This creature deals combat damage before creatures without first strike.'),
    ('double strike', 'Deals both first-strike and normal damage', 'A creature with double strike deals combat damage twice per combat phase.', TRUE, FALSE, FALSE, 'This creature deals both first-strike and regular combat damage.'),
    ('deathtouch', 'Any damage kills creature', 'Any amount of damage dealt by a source with deathtouch is enough to destroy a creature.', TRUE, FALSE, FALSE, 'Any amount of damage this deals to a creature is enough to destroy it.'),
    ('defender', 'Cannot attack', 'A creature with defender cannot attack.', TRUE, FALSE, FALSE, 'This creature can''t attack.'),
    ('haste', 'Can attack immediately', 'A creature with haste can attack and tap the turn it enters the battlefield.', TRUE, FALSE, FALSE, 'This creature can attack and {T} as soon as it enters.'),
    ('hexproof', 'Cannot be targeted by opponents', 'A permanent with hexproof cannot be the target of spells or abilities your opponents control.', TRUE, FALSE, FALSE, 'This permanent can''t be the target of spells or abilities your opponents control.'),
    ('indestructible', 'Cannot be destroyed', 'Permanents with indestructible cannot be destroyed by damage or effects that say "destroy."', TRUE, FALSE, FALSE, 'Damage and effects that say "destroy" don''t destroy this permanent.'),
    ('lifelink', 'Damage causes life gain', 'Damage dealt by a source with lifelink causes that source''s controller to gain that much life.', TRUE, FALSE, FALSE, 'Damage dealt by this creature also causes you to gain that much life.'),
    ('menace', 'Must be blocked by multiple creatures', 'A creature with menace can''t be blocked except by two or more creatures.', TRUE, FALSE, FALSE, 'This creature can''t be blocked except by two or more creatures.'),
    ('reach', 'Can block flying creatures', 'A creature with reach can block creatures with flying.', TRUE, FALSE, FALSE, 'This creature can block creatures with flying.'),
    ('trample', 'Excess damage hits player', 'A creature with trample can deal excess combat damage to the player or planeswalker it''s attacking.', TRUE, FALSE, FALSE, 'This creature can deal excess combat damage to the player or planeswalker it''s attacking.'),
    ('vigilance', 'Doesn''t tap to attack', 'Attacking doesn''t cause creatures with vigilance to tap.', TRUE, FALSE, FALSE, 'Attacking doesn''t cause this creature to tap.'),
    ('ward', 'Costs mana to target', 'Whenever a permanent with ward becomes the target of a spell or ability an opponent controls, counter that spell or ability unless that player pays the ward cost.', TRUE, FALSE, TRUE, 'Whenever this permanent becomes the target of a spell or ability an opponent controls, counter it unless that player pays {X}.'),
    ('flash', 'Can be cast at instant speed', 'A spell with flash can be cast any time you could cast an instant.', TRUE, FALSE, FALSE, 'You may cast this spell any time you could cast an instant.')
ON CONFLICT (keyword) DO NOTHING;


COMMIT;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

DO $$
DECLARE
    cat_count INTEGER;
    rule_count INTEGER;
    keyword_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cat_count FROM rule_categories;
    SELECT COUNT(*) INTO rule_count FROM rules;
    SELECT COUNT(*) INTO keyword_count FROM keyword_abilities;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Seed Rules Loaded Successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Rule Categories: %', cat_count;
    RAISE NOTICE 'Rules: %', rule_count;
    RAISE NOTICE 'Keyword Abilities: %', keyword_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Generate embeddings: python generate_embeddings_dual.py';
    RAISE NOTICE '2. Extract more rules: python extract_rules.py';
    RAISE NOTICE '========================================';
END $$;
