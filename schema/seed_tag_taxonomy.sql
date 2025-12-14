-- ============================================================================
-- Seed Tag Taxonomy
-- ============================================================================
-- Initial tag categories and tags for MTG card functional tagging
-- ============================================================================

-- ============================================================================
-- TAG CATEGORIES
-- ============================================================================

INSERT INTO tag_categories (name, display_name, description, sort_order) VALUES
('resource_generation', 'Resource Generation', 'Cards that generate resources (mana, cards, tokens)', 1),
('resource_cost', 'Resource Costs', 'Cards that require specific costs or sacrifices', 2),
('state_change', 'State Changes', 'Cards that modify game state (untap, blink, bounce)', 3),
('triggers', 'Triggers', 'Cards with triggered abilities', 4),
('effects', 'Effects', 'Specific effects cards create', 5),
('card_types', 'Card Types', 'Structural card type tags', 6),
('combo_enablers', 'Combo Enablers', 'Cards that enable infinite loops', 7),
('win_conditions', 'Win Conditions', 'Cards that win or end the game', 8),
('protection', 'Protection', 'Cards that protect permanents or prevent effects', 9),
('removal', 'Removal', 'Cards that remove or neutralize permanents', 10);

-- ============================================================================
-- ROOT TAGS
-- ============================================================================

-- RESOURCE GENERATION (parent tags)
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
-- Mana generation
('generates_mana', 'Generates Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces mana of any type', 0, ARRAY['generates_mana'], true),

-- Card advantage
('draws_cards', 'Draws Cards',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Draws one or more cards', 0, ARRAY['draws_cards'], true),

-- Tokens
('creates_tokens', 'Creates Tokens',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Creates creature or other tokens', 0, ARRAY['creates_tokens'], true),

-- Tutoring
('searches_library', 'Searches Library',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Tutors cards from library', 0, ARRAY['searches_library'], true),

-- Recursion
('reanimates', 'Reanimates',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Returns creatures from graveyard to battlefield', 0, ARRAY['reanimates'], true);

-- CHILD TAGS: Mana Generation (specific colors)
INSERT INTO tags (name, display_name, category_id, description, parent_tag_id, depth, path) VALUES
('generates_white_mana', 'Generates White Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces white mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_white_mana']),

('generates_blue_mana', 'Generates Blue Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces blue mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_blue_mana']),

('generates_black_mana', 'Generates Black Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces black mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_black_mana']),

('generates_red_mana', 'Generates Red Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces red mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_red_mana']),

('generates_green_mana', 'Generates Green Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces green mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_green_mana']),

('generates_colorless_mana', 'Generates Colorless Mana',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    'Produces colorless mana',
    (SELECT id FROM tags WHERE name = 'generates_mana'),
    1, ARRAY['generates_mana', 'generates_colorless_mana']);

-- RESOURCE COSTS
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('sacrifices_creatures', 'Sacrifices Creatures',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires sacrificing creatures', 0, ARRAY['sacrifices_creatures'], true),

('sacrifices_artifacts', 'Sacrifices Artifacts',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires sacrificing artifacts', 0, ARRAY['sacrifices_artifacts'], true),

('sacrifices_enchantments', 'Sacrifices Enchantments',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires sacrificing enchantments', 0, ARRAY['sacrifices_enchantments'], true),

('sacrifices_permanents', 'Sacrifices Permanents',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Sacrifices any permanent type', 0, ARRAY['sacrifices_permanents'], true),

('discards_cards', 'Discards Cards',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires discarding cards', 0, ARRAY['discards_cards'], true),

('pays_life', 'Pays Life',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Costs life to activate/cast', 0, ARRAY['pays_life'], true),

('taps_permanents', 'Taps Permanents',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires tapping permanents', 0, ARRAY['taps_permanents'], true),

('exiles_cards', 'Exiles Cards as Cost',
    (SELECT id FROM tag_categories WHERE name = 'resource_cost'),
    'Requires exiling cards as a cost', 0, ARRAY['exiles_cards'], true);

-- STATE CHANGES (crucial for combos)
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('untaps_permanents', 'Untaps Permanents',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Untaps one or more permanents', 0, ARRAY['untaps_permanents'], true),

('blinks_creatures', 'Blinks Creatures',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Exiles and returns creatures', 0, ARRAY['blinks_creatures'], true),

('bounces_permanents', 'Bounces Permanents',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Returns permanents to hand/library', 0, ARRAY['bounces_permanents'], true),

('copies_spells', 'Copies Spells',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Creates copies of spells', 0, ARRAY['copies_spells'], true),

('reduces_costs', 'Reduces Costs',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Makes spells/abilities cost less', 0, ARRAY['reduces_costs'], true),

('grants_abilities', 'Grants Abilities',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Gives abilities to other cards', 0, ARRAY['grants_abilities'], true),

('transforms_permanents', 'Transforms Permanents',
    (SELECT id FROM tag_categories WHERE name = 'state_change'),
    'Changes permanent types or characteristics', 0, ARRAY['transforms_permanents'], true);

-- TRIGGERS (very important for combos)
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('triggers_on_etb', 'Triggers on ETB',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when permanents enter battlefield', 0, ARRAY['triggers_on_etb'], true),

('triggers_on_death', 'Triggers on Death',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when creatures die', 0, ARRAY['triggers_on_death'], true),

('triggers_on_ltb', 'Triggers on LTB',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when permanents leave battlefield', 0, ARRAY['triggers_on_ltb'], true),

('triggers_on_cast', 'Triggers on Cast',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when spells are cast', 0, ARRAY['triggers_on_cast'], true),

('triggers_on_draw', 'Triggers on Draw',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when drawing cards', 0, ARRAY['triggers_on_draw'], true),

('triggers_on_attack', 'Triggers on Attack',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when attacking', 0, ARRAY['triggers_on_attack'], true),

('triggers_on_tap', 'Triggers on Tap',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when permanents become tapped', 0, ARRAY['triggers_on_tap'], true),

('triggers_on_untap', 'Triggers on Untap',
    (SELECT id FROM tag_categories WHERE name = 'triggers'),
    'Triggers when permanents untap', 0, ARRAY['triggers_on_untap'], true);

-- EFFECTS
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('drains_life', 'Drains Life',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Causes opponents to lose life', 0, ARRAY['drains_life'], true),

('gains_life', 'Gains Life',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Causes controller to gain life', 0, ARRAY['gains_life'], true),

('mills_library', 'Mills Library',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Puts cards from library to graveyard', 0, ARRAY['mills_library'], true),

('deals_damage', 'Deals Damage',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Directly deals damage', 0, ARRAY['deals_damage'], true),

('destroys_permanents', 'Destroys Permanents',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Destroys permanents', 0, ARRAY['destroys_permanents'], true),

('counters_spells', 'Counters Spells',
    (SELECT id FROM tag_categories WHERE name = 'effects'),
    'Counters spells or abilities', 0, ARRAY['counters_spells'], true);

-- COMBO ENABLERS (meta tags for combo discovery)
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('infinite_enabler', 'Infinite Enabler',
    (SELECT id FROM tag_categories WHERE name = 'combo_enablers'),
    'Commonly enables infinite combos', 0, ARRAY['infinite_enabler'], true),

('loop_component', 'Loop Component',
    (SELECT id FROM tag_categories WHERE name = 'combo_enablers'),
    'Part of common loops', 0, ARRAY['loop_component'], true),

('cost_reducer', 'Cost Reducer',
    (SELECT id FROM tag_categories WHERE name = 'combo_enablers'),
    'Makes combos cheaper to execute', 0, ARRAY['cost_reducer'], true),

('free_spell', 'Free Spell',
    (SELECT id FROM tag_categories WHERE name = 'combo_enablers'),
    'Can be cast for free or zero mana', 0, ARRAY['free_spell'], true);

-- WIN CONDITIONS
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('alternate_win_con', 'Alternate Win Condition',
    (SELECT id FROM tag_categories WHERE name = 'win_conditions'),
    'Wins through alternate means', 0, ARRAY['alternate_win_con'], true),

('wins_with_empty_library', 'Wins with Empty Library',
    (SELECT id FROM tag_categories WHERE name = 'win_conditions'),
    'Wins when library is empty', 0, ARRAY['wins_with_empty_library'], true),

('wins_with_condition', 'Wins with Condition',
    (SELECT id FROM tag_categories WHERE name = 'win_conditions'),
    'Wins when specific condition met', 0, ARRAY['wins_with_condition'], true),

('causes_opponent_loss', 'Causes Opponent Loss',
    (SELECT id FROM tag_categories WHERE name = 'win_conditions'),
    'Makes opponent lose through various means', 0, ARRAY['causes_opponent_loss'], true);

-- PROTECTION
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('grants_hexproof', 'Grants Hexproof',
    (SELECT id FROM tag_categories WHERE name = 'protection'),
    'Gives hexproof to permanents', 0, ARRAY['grants_hexproof'], false),

('grants_shroud', 'Grants Shroud',
    (SELECT id FROM tag_categories WHERE name = 'protection'),
    'Gives shroud to permanents', 0, ARRAY['grants_shroud'], false),

('grants_indestructible', 'Grants Indestructible',
    (SELECT id FROM tag_categories WHERE name = 'protection'),
    'Makes permanents indestructible', 0, ARRAY['grants_indestructible'], false),

('grants_protection', 'Grants Protection',
    (SELECT id FROM tag_categories WHERE name = 'protection'),
    'Gives protection from X', 0, ARRAY['grants_protection'], false);

-- REMOVAL
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('destroys_creatures', 'Destroys Creatures',
    (SELECT id FROM tag_categories WHERE name = 'removal'),
    'Destroys creature permanents', 0, ARRAY['destroys_creatures'], false),

('destroys_artifacts', 'Destroys Artifacts',
    (SELECT id FROM tag_categories WHERE name = 'removal'),
    'Destroys artifact permanents', 0, ARRAY['destroys_artifacts'], false),

('destroys_enchantments', 'Destroys Enchantments',
    (SELECT id FROM tag_categories WHERE name = 'removal'),
    'Destroys enchantment permanents', 0, ARRAY['destroys_enchantments'], false),

('exiles_permanents', 'Exiles Permanents',
    (SELECT id FROM tag_categories WHERE name = 'removal'),
    'Exiles permanents (as an effect, not cost)', 0, ARRAY['exiles_permanents'], false);

-- CARD TYPES (structural tags)
INSERT INTO tags (name, display_name, category_id, description, depth, path, is_combo_relevant) VALUES
('creature', 'Creature',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Creature card', 0, ARRAY['creature'], false),

('artifact', 'Artifact',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Artifact card', 0, ARRAY['artifact'], false),

('enchantment', 'Enchantment',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Enchantment card', 0, ARRAY['enchantment'], false),

('instant', 'Instant',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Instant card', 0, ARRAY['instant'], false),

('sorcery', 'Sorcery',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Sorcery card', 0, ARRAY['sorcery'], false),

('planeswalker', 'Planeswalker',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Planeswalker card', 0, ARRAY['planeswalker'], false),

('land', 'Land',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Land card', 0, ARRAY['land'], false),

('aura', 'Aura',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Aura subtype', 0, ARRAY['aura'], false),

('equipment', 'Equipment',
    (SELECT id FROM tag_categories WHERE name = 'card_types'),
    'Equipment subtype', 0, ARRAY['equipment'], false);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show tag hierarchy
SELECT
    LPAD('', depth * 2, ' ') || display_name as tag_hierarchy,
    tc.display_name as category,
    is_combo_relevant
FROM tags t
JOIN tag_categories tc ON t.category_id = tc.id
ORDER BY tc.sort_order, t.path;

-- Show tag counts
SELECT
    tc.display_name as category,
    COUNT(*) as tag_count
FROM tags t
JOIN tag_categories tc ON t.category_id = tc.id
GROUP BY tc.id, tc.display_name, tc.sort_order
ORDER BY tc.sort_order;

-- Show combo-relevant tags
SELECT
    tc.display_name as category,
    t.display_name as tag,
    t.depth
FROM tags t
JOIN tag_categories tc ON t.category_id = tc.id
WHERE t.is_combo_relevant = true
ORDER BY tc.sort_order, t.depth, t.display_name;
