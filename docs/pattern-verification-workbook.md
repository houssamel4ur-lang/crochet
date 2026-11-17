# Crochet physical testing and image verification — November 17, 2026

**Purpose:** An AI concept, a plausible stitch count, or a written pattern draft is not proof of a physically completed crochet sample. This tracker makes that distinction visible and prevents an unverified pattern from silently acquiring a "Tested" label.

## Current evidence
- No physically tested records have been entered into `content/pattern_testing_records.json`. This means **no pattern is independently certified by this tracker**. It does not assert that an owner has never made a sample elsewhere.
- All existing article slugs and content remain unchanged except for the new curated homepage and SEO preview text.
- The original ad code and image files have not been altered.

## Before marking a pattern as tested
1. Crochet the exact instructions from start to finish using recorded yarn, hook size and tension.
2. Verify each row/round count, component count, assembly, finished dimensions and relevant safety points.
3. Take your own photograph of the real sample and save a WebP at `assets/verified-samples/<slug>-finished.webp`. It must actually depict the item made from the instructions.
4. Update `content/pattern_testing_records.json` under `verified_patterns` with a record that includes:
   - `status: "tested"`
   - `physical_sample_completed: true`
   - `stitch_counts_checked: true`
   - `tested_by`: real tester name
   - `tested_at`: actual ISO date
   - `materials_used`: exact yarn/hook
   - `finished_measurements`: measured physical dimensions
   - `test_notes`: any corrections or departures
5. Regenerate SEO pages. Only then may the code hide the construction draft note; if any evidence is missing, the note remains.
6. Update a hero image only with the authentic photo, maintaining truthful captions for any remaining concept images. Verify safety for child-contact items separately.

## Published-article proof tracker — all 53 URLs
Each unchecked item needs an evidence record before the website can describe that specific written pattern as physically tested.

- [ ] [capybara-amigurumi-free-crochet-pattern](https://cozyloops.site/posts/capybara-amigurumi-free-crochet-pattern/) — physical sample and source photo not verified in registry
- [ ] [crochet-aloe-inspired-windowsill-plant](https://cozyloops.site/posts/crochet-aloe-inspired-windowsill-plant/) — physical sample and source photo not verified in registry
- [ ] [crochet-baby-animal-hats-bear-bunny-frog-guide](https://cozyloops.site/posts/crochet-baby-animal-hats-bear-bunny-frog-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-baby-booties-sizing-sole-guide](https://cozyloops.site/posts/crochet-baby-booties-sizing-sole-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-bow-keychain-free-pattern](https://cozyloops.site/posts/crochet-bow-keychain-free-pattern/) — physical sample and source photo not verified in registry
- [ ] [crochet-bucket-hat-for-beginners](https://cozyloops.site/posts/crochet-bucket-hat-for-beginners/) — physical sample and source photo not verified in registry
- [ ] [crochet-butterfly-ornament-wing-guide](https://cozyloops.site/posts/crochet-butterfly-ornament-wing-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-clam-shell-ring-presentation-pad](https://cozyloops.site/posts/crochet-clam-shell-ring-presentation-pad/) — physical sample and source photo not verified in registry
- [ ] [crochet-daisy-flower-bookmark-free-pattern](https://cozyloops.site/posts/crochet-daisy-flower-bookmark-free-pattern/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-bed-runner](https://cozyloops.site/posts/crochet-dollhouse-bed-runner/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-bolster-cushion](https://cozyloops.site/posts/crochet-dollhouse-bolster-cushion/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-cafe-awning](https://cozyloops.site/posts/crochet-dollhouse-cafe-awning/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-market-basket](https://cozyloops.site/posts/crochet-dollhouse-market-basket/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-picnic-blanket](https://cozyloops.site/posts/crochet-dollhouse-picnic-blanket/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-reading-rug](https://cozyloops.site/posts/crochet-dollhouse-reading-rug/) — physical sample and source photo not verified in registry
- [ ] [crochet-dollhouse-round-pouf](https://cozyloops.site/posts/crochet-dollhouse-round-pouf/) — physical sample and source photo not verified in registry
- [ ] [crochet-eucalyptus-place-setting-sprig](https://cozyloops.site/posts/crochet-eucalyptus-place-setting-sprig/) — physical sample and source photo not verified in registry
- [ ] [crochet-fan-palm-for-a-bookshelf](https://cozyloops.site/posts/crochet-fan-palm-for-a-bookshelf/) — physical sample and source photo not verified in registry
- [ ] [crochet-fern-frond-bookmark](https://cozyloops.site/posts/crochet-fern-frond-bookmark/) — physical sample and source photo not verified in registry
- [ ] [crochet-flower-coasters-free-pattern](https://cozyloops.site/posts/crochet-flower-coasters-free-pattern/) — physical sample and source photo not verified in registry
- [ ] [crochet-flower-keychains-scrap-yarn-guide](https://cozyloops.site/posts/crochet-flower-keychains-scrap-yarn-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-hanging-pea-vine-shelf-ornament](https://cozyloops.site/posts/crochet-hanging-pea-vine-shelf-ornament/) — physical sample and source photo not verified in registry
- [ ] [crochet-jellyfish-for-a-desktop-display](https://cozyloops.site/posts/crochet-jellyfish-for-a-desktop-display/) — physical sample and source photo not verified in registry
- [ ] [crochet-kelp-book-nook-panel](https://cozyloops.site/posts/crochet-kelp-book-nook-panel/) — physical sample and source photo not verified in registry
- [ ] [crochet-lavender-sachet-cover](https://cozyloops.site/posts/crochet-lavender-sachet-cover/) — physical sample and source photo not verified in registry
- [ ] [crochet-lithops-pebble-garden](https://cozyloops.site/posts/crochet-lithops-pebble-garden/) — physical sample and source photo not verified in registry
- [ ] [crochet-manta-ray-applique-for-a-coastal-cushion](https://cozyloops.site/posts/crochet-manta-ray-applique-for-a-coastal-cushion/) — physical sample and source photo not verified in registry
- [ ] [crochet-monstera-inspired-leaf-wall-tile](https://cozyloops.site/posts/crochet-monstera-inspired-leaf-wall-tile/) — physical sample and source photo not verified in registry
- [ ] [crochet-moss-and-mushroom-terrarium-insert](https://cozyloops.site/posts/crochet-moss-and-mushroom-terrarium-insert/) — physical sample and source photo not verified in registry
- [ ] [crochet-nautilus-inspired-spiral-medallion](https://cozyloops.site/posts/crochet-nautilus-inspired-spiral-medallion/) — physical sample and source photo not verified in registry
- [ ] [crochet-oyster-and-pearl-keepsake-display](https://cozyloops.site/posts/crochet-oyster-and-pearl-keepsake-display/) — physical sample and source photo not verified in registry
- [ ] [crochet-patterns-for-beginners-guide](https://cozyloops.site/posts/crochet-patterns-for-beginners-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-penguin-ornament-free-pattern](https://cozyloops.site/posts/crochet-penguin-ornament-free-pattern/) — physical sample and source photo not verified in registry
- [ ] [crochet-phone-pouch-crossbody-size-guide](https://cozyloops.site/posts/crochet-phone-pouch-crossbody-size-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-plant-hanger-beginners](https://cozyloops.site/posts/crochet-plant-hanger-beginners/) — physical sample and source photo not verified in registry
- [ ] [crochet-sea-urchin-desk-ornament](https://cozyloops.site/posts/crochet-sea-urchin-desk-ornament/) — physical sample and source photo not verified in registry
- [ ] [crochet-seahorse-silhouette-wall-pennant](https://cozyloops.site/posts/crochet-seahorse-silhouette-wall-pennant/) — physical sample and source photo not verified in registry
- [ ] [crochet-strawberry-crossbody-bag-guide](https://cozyloops.site/posts/crochet-strawberry-crossbody-bag-guide/) — physical sample and source photo not verified in registry
- [ ] [crochet-string-of-hearts-desk-planter](https://cozyloops.site/posts/crochet-string-of-hearts-desk-planter/) — physical sample and source photo not verified in registry
- [ ] [crochet-tide-pool-limpets-on-a-pebble-mat](https://cozyloops.site/posts/crochet-tide-pool-limpets-on-a-pebble-mat/) — physical sample and source photo not verified in registry
- [ ] [crochet-tulip-bouquet-stems-guide](https://cozyloops.site/posts/crochet-tulip-bouquet-stems-guide/) — physical sample and source photo not verified in registry
- [ ] [daisy-granny-square-blanket-guide](https://cozyloops.site/posts/daisy-granny-square-blanket-guide/) — physical sample and source photo not verified in registry
- [ ] [easy-crochet-beanie-pattern](https://cozyloops.site/posts/easy-crochet-beanie-pattern/) — physical sample and source photo not verified in registry
- [ ] [easy-crochet-scarf-for-beginners](https://cozyloops.site/posts/easy-crochet-scarf-for-beginners/) — physical sample and source photo not verified in registry
- [ ] [mini-crochet-coral-garden-in-a-bowl](https://cozyloops.site/posts/mini-crochet-coral-garden-in-a-bowl/) — physical sample and source photo not verified in registry
- [ ] [mini-crochet-dinosaur-amigurumi-guide](https://cozyloops.site/posts/mini-crochet-dinosaur-amigurumi-guide/) — physical sample and source photo not verified in registry
- [ ] [mini-farm-animals-amigurumi-collection](https://cozyloops.site/posts/mini-farm-animals-amigurumi-collection/) — physical sample and source photo not verified in registry
- [ ] [mini-ocean-amigurumi-free-crochet-patterns](https://cozyloops.site/posts/mini-ocean-amigurumi-free-crochet-patterns/) — physical sample and source photo not verified in registry
- [ ] [mini-ocean-amigurumi-keychains-free-patterns](https://cozyloops.site/posts/mini-ocean-amigurumi-keychains-free-patterns/) — physical sample and source photo not verified in registry
- [ ] [mini-woodland-amigurumi-animal-ideas](https://cozyloops.site/posts/mini-woodland-amigurumi-animal-ideas/) — physical sample and source photo not verified in registry
- [ ] [pink-axolotl-crochet-amigurumi-guide](https://cozyloops.site/posts/pink-axolotl-crochet-amigurumi-guide/) — physical sample and source photo not verified in registry
- [ ] [starfish-baby-crochet-outfit-guide](https://cozyloops.site/posts/starfish-baby-crochet-outfit-guide/) — physical sample and source photo not verified in registry
- [ ] [sunflower-crochet-tote-bag-guide](https://cozyloops.site/posts/sunflower-crochet-tote-bag-guide/) — physical sample and source photo not verified in registry

## Follow-up editorial review
- Remove inaccurate/duplicated boilerplate only when meaning is preserved.
- Correct instructions using real making notes, never by guessing stitch counts.
- Replace AI concept photos with real project photography progressively.
- If you have an author portrait, add only an authentic user-approved image; an initials avatar remains preferable to a fabricated identity.
