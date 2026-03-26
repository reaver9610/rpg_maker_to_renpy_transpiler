# RPG Maker MV Map System Specification

> **Companion Document** — This document complements `RPG Maker MV Map Data Structure.md` by covering `System.json` and the relationship between map data and global game state.

---

## Table of Contents

1. [Overview](#1-overview)
2. [System.json Structure](#2-systemjson-structure)
3. [Game Identity](#3-game-identity)
4. [Switches](#4-switches)
5. [Variables](#5-variables)
6. [Stat System (terms.params)](#6-stat-system-termsparams)
7. [Basic Terms (terms.basic)](#7-basic-terms-termsbasic)
8. [Terms Commands](#8-terms-commands)
9. [Terms Messages](#9-terms-messages)
10. [Map ↔ System Relationship](#10-map--system-relationship)
11. [Cross-Reference: Map001.json](#11-cross-reference-map001json)
12. [Missing Data Files](#12-missing-data-files)

---

## 1. Overview

`System.json` is the central configuration file for an RPG Maker MV project. It contains:

- Game metadata (title, currency, locale)
- Global state definitions (switches, variables)
- Localization terms (stat names, UI labels, messages)
- Party configuration
- Battle and system settings

**For the transpiler**, `System.json` provides the human-readable names that map numeric switch/variable IDs to meaningful labels, enabling generation of readable Ren'Py code with comments and descriptive variable names.

---

## 2. System.json Structure

| Key | Type | Description |
|---|---|---|
| `gameTitle` | `string` | Game display title |
| `currencyUnit` | `string` | Currency name (with leading space) |
| `locale` | `string` | Language/locale code |
| `startMapId` | `int` | Starting map ID |
| `startX` | `int` | Starting X coordinate |
| `startY` | `int` | Starting Y coordinate |
| `partyMembers` | `list[int]` | Actor IDs in starting party |
| `switches` | `list[string]` | Switch names (1-indexed, index 0 = empty) |
| `variables` | `list[string]` | Variable names (1-indexed, index 0 = empty) |
| `terms` | `object` | Localization terms (basic, params, commands, messages) |
| `sounds` | `list[object]` | Sound effect definitions |
| `skillTypes` | `list[string]` | Skill type names |
| `menuCommands` | `list[bool]` | Menu visibility flags |
| `opt*` | `bool` | Various engine options |
| `battleBgm` | `object` | Battle BGM |
| `battleback1Name` | `string` | Battle background layer 1 |
| `battleback2Name` | `string` | Battle background layer 2 |
| `title1Name` | `string` | Title screen image 1 |
| `title2Name` | `string` | Title screen image 2 |
| `titleBgm` | `object` | Title screen music |
| `windowTone` | `list[int]` | RGBA window color tone |
| `airship`, `ship`, `boat` | `object` | Vehicle configurations |

---

## 3. Game Identity

**From the test project (Claire's Quest 0.29.1):**

| Field | Value |
|---|---|
| `gameTitle` | "Claire's Quest 0.29.1" |
| `currencyUnit` | " Silvers" |
| `locale` | "en_US" |
| `startMapId` | 30 |
| `startX` | 4 |
| `startY` | 4 |
| `partyMembers` | [1, 2, 3, 4] |

---

## 4. Switches

**Total**: 1,100 switches (index 1–1100)  
**Named**: 1,070 switches  
**Unused/Empty**: 30 switches

Switch index 0 is always empty (placeholder for 1-based RPG Maker indexing).

### 4.1 Categorized Inventory

#### Quest/Mission Flags (`M:` prefix)

| ID | Name |
|---|---|
| 21 | "M: Find the purse" |
| 22 | "M: Pay up or alternate entry" |
| 23 | "M: Go find Gregory" |
| 24 | "M: Pass a message" |
| 25 | "M: Wounded refugee" |
| 26 | "M: Get into the fort" |
| 27 | "M: Find Hookton entry" |
| 28 | "M: Find a ship" |
| 29 | "M: Get money for sailor" |
| 30 | "M: Captain Grey" |
| 31 | "M: Find Marie" |
| 32 | "M: Get out of fort" |
| 33 | "M: Learning thief" |
| 34 | "M: Find Bjorn" |
| 35 | "M: Dyrios and Rylar" |
| 36 | "M: Rescue Natalie" |
| 37 | "M: Runaway Lovers" |
| 38 | "M: Look around ship" |
| 39 | "M: Deal w/ Hamley" |
| 40 | "M: Rathpike basement" |
| 141 | "M: Investigate Narfu " |
| 142 | "M: Fat Jack" |
| 143 | "M: Narfu Fish" |
| 144 | "M: Condolences" |
| 145 | "M: Narfu posting" |
| 146 | "M: Earn Belisaros's trust" |
| 147 | "M: Sailor's Charm" |
| 148 | "M: Ghosted Man" |
| 149 | "M: Heatherly Quest" |
| 150 | "M: Food for Refugees" |
| 151 | "M: Pick Bramblerose" |
| 152 | "M: Become Esther" |
| 153 | "M: Investigate cell" |
| 154 | "M: Gilly" |
| 155 | "M: Meet in grave" |
| 156 | "M: Meeting Narfu" |
| 157 | "M: Meet the Sisters" |
| 158 | "M: Attend to Lily" |
| 159 | "M: Valos Lighthouse" |
| 160 | "M: Ranger 2" |
| 341 | "M: Mushroom Time" |
| 342 | "M: Choose sister path" |
| 343 | "M: Report to Rose" |
| 344 | "M: Help Karland Books" |
| 345 | "M: Rose in Temple" |
| 346 | "M: Kindling" |

#### Scene/Sexual Flags (`S:` prefix)

| ID | Name |
|---|---|
| 61 | "S: Guard Blowjob" |
| 62 | "S: Old Man Grope" |
| 63 | "S: Mean Refugee" |
| 64 | "S: Horse Handjob" |
| 65 | "S: Hookton Inn" |
| 66 | "S: Rathpike Inn" |
| 67 | "S: Fort" |
| 68 | "S: Pirates" |
| 69 | "S: Brothel #2" |
| 70 | "S: Brothel #1" |
| 71 | "S: Rose #1" |
| 72 | "S: Chef Spank" |
| 73 | "S: Horse Blowjob" |
| 74 | "S: Rose #2" |
| 75 | "S: Stalker" |
| 76 | "S: Guard Dog" |
| 77 | "S: Kennel Dogs" |
| 78 | "S: Gilly Pigboss" |
| 79 | "S: Slave Claire BJ" |
| 80 | "S: Meat Pit BJ" |
| 281 | "S: Baker's Boy" |
| 282 | "S: Meat Pit 2" |
| 283 | "S: Stable Final" |
| 284 | "S: Sally" |
| 285 | "S: Ghost" |
| 286 | "S: Boar" |
| 287 | "S: Lawrence Fondle" |
| 288 | "S: Meat Pit 3" |
| 289 | "S: Shroomer" |
| 290 | "S: Nun Blowjob" |
| 291 | "S: Rose Anal" |
| 292 | "S: Lawrence Penetrates" |
| 293 | "S: Lawrence Finale" |
| 294 | "S: Fairfelt 3some" |
| 295 | "S: Groping" |
| 296 | "S: Barmaid" |
| 297 | "S: Titjob" |
| 298 | "S: Rose massage" |
| 299 | "S: Possessed shota" |
| 300 | "S: Andumas" |
| 347 | "S: Mountain lion" |
| 348 | "S: Wolves" |
| 349 | "S: Sister Lily" |
| 350 | "S: Emily" |
| 351 | "S: Rose Bondage" |
| 352 | "S: Bubba Bear" |
| 353 | "S: The Club" |
| 354 | "S: Pissplay" |
| 355 | "S: Handjob" |
| 356 | "S: Evilshotas" |
| 357 | "S: Bull BJ" |
| 358 | "S: Bullbang" |
| 359 | "S: Thugchoke" |
| 360 | "S: Bath orgy" |
| 361 | "S: Rose blowjob training" |
| 362 | "S: Rose pussy training" |
| 363 | "S: Rose anal training" |
| 501 | "S: Shota Manticore" |
| 502 | "S: Merc ambush" |
| 503 | "S: Kabedon" |
| 504 | "S: Sub Nymph" |
| 505 | "S: Dom Nymph" |
| 506 | "S: Isobelle is Beastwife" |
| 507 | "S: Isobelle Anal Dildo" |
| 508 | "S: Werewolf" |
| 509 | "S: Rain Paupers" |
| 510 | "S: Charlotte Grope" |
| 511 | "S: BethxGale Voyeur" |
| 512 | "S: Aiyana Lesbian" |
| 513 | "S: Fairy fucking (Claire dom)" |
| 514 | "S: Fairy fucking (Claire sub)" |
| 515 | "S: Charlotte jobhunt" |
| 516 | "S: Alligator" |
| 517 | "S: Gauntlet Urchins" |
| 518 | "S: Harvest festival (sub)" |
| 519 | "S: Harvest festival (dom)" |
| 520 | "S: Wallstuck thieves" |
| 701 | "S: Genevieve badend" |
| 702 | "S: Showgirls intro" |
| 703 | "S: Jillian badend" |
| 704 | "S: oldman assgrope" |
| 705 | "S: Stella" |
| 706 | "S: Marie x Pigboss" |
| 707 | "S: Thieves DP" |
| 708 | "S: MiaMakeout" |
| 709 | "S: Maude+Hyena" |
| 710 | "S: SoFPrison" |
| 711 | "S: Oak Tree" |
| 712 | "S: TigerRox + Monkes" |
| 713 | "S: CharClaire Ride " |
| 714 | "S: CharBell Ride" |
| 715 | "S: ClaireLeon Bath" |
| 716 | "S: ClaireBell Bath" |
| 717 | "S: Gold Floor" |
| 718 | "S: Naptime" |
| 719 | "S: Lily Shrew Approach" |
| 720 | "S: Rose Shrew Approach" |
| 881 | "S: Sinn-sith" |
| 882 | "S: BellevuetheAssMan" |
| 883 | "S: Under the table" |
| 884 | "S: All in the family" |
| 885 | "S: BrutusXEvelyn voyeur" |
| 886 | "S: Satyrs" |
| 887 | "S: ClashofFaiths" |
| 888 | "S: Basilisk" |
| 889 | "S: Ranger Finish" |
| 890 | "S: Beth Dildo" |
| 891 | "S: Futa Gangbang" |
| 892 | "S: Peony GB Reversal" |
| 893 | "S: Peony femdom" |
| 894 | "S: Andumas #1" |
| 895 | "S: Andumas" |
| 896 | "S: Pauper Gang" |
| 897 | "S: Pauper Gang Upgrade" |

#### Story Progression Flags

| ID | Name |
|---|---|
| 1 | "Camp entry obtained" |
| 2 | "Spoke to skipper" |
| 3 | "Camp entry stopped" |
| 4 | "Spoke to bruders" |
| 5 | "Paid the smuggler" |
| 6 | "The fort escape" |
| 7 | "Moved Hookton table" |
| 8 | "Finding Marie" |
| 9 | "Inspired Beth" |
| 10 | "Spoke to Beth" |
| 11 | "Tortured" |
| 12 | "Grateful youth opens shop" |
| 13 | "Grateful youth depressed" |
| 14 | "Killed a man" |
| 15 | "Learned to lockpick" |
| 16 | "Took Grey's route" |
| 17 | "Killed mean refugee" |
| 18 | "Blowjob witnessed" |
| 19 | "Robbed Hamley" |
| 20 | "Donated to a beggar" |
| 41 | "IN GALLERY" |
| 42 | "Store on fire" |
| 43 | "Pirates" |
| 44 | "Horse witnessed" |
| 45 | "Helped baker" |
| 46 | "Hookton working" |
| 47 | "Bakerwoman laundry" |
| 48 | "Bakerwoman sheets" |
| 49 | "Work done " |
| 50 | "Blow peeper" |
| 51 | "Freestay Hookton" |
| 52 | "Shanghai'd" |
| 53 | "Grave robber" |
| 54 | "Outwitted Swoggy" |
| 55 | "Had dinner w/ baker" |
| 56 | "Giving blowjob" |
| 57 | "Indentured servitude" |
| 58 | "Permission to leave" |
| 59 | "Ate food" |
| 60 | "Round 2" |
| 81 | "Restituition" |
| 82 | "Natalie in room" |
| 83 | "Salim in room" |
| 84 | "Pre-work Pit" |
| 85 | "Working pit" |
| 86 | "Won over Emma" |
| 87 | "Won over Natalie" |
| 88 | "Sarah info" |
| 89 | "Zayana info" |
| 90 | "Sarah skills" |
| 91 | "Zayana skills" |
| 92 | "Customer didn't cum" |
| 93 | "Lawrence in room" |
| 94 | "Round 3" |
| 95 | "Met Esther" |
| 96 | "Met Chad" |
| 97 | "Stole lockbox" |
| 98 | "Joined Thieves" |
| 99 | "Chad gives entry" |
| 100 | "Thief Quest 1" |
| 101 | "Meat Pit liberated" |
| 102 | "Thief Quest 2" |
| 103 | "Housekeeping" |
| 104 | "Room 1 done" |
| 105 | "Room 2 done" |
| 106 | "Room 3 done" |
| 107 | "Room 4 done" |
| 108 | "Room 5 started" |
| 109 | "Room 5 done" |
| 110 | "Room 6 done" |
| 111 | "Angered unpleasant man" |
| 112 | "Pain in the ass" |
| 113 | "Enjoyed anal" |
| 114 | "Pit Champion" |
| 115 | "Trafficking unlocked" |
| 116 | "Returned necklace" |
| 117 | "Whoresbane knowledge" |
| 118 | "Suspicious pub" |
| 119 | "Spoke to Rylar" |
| 120 | "Foreman not at desk" |
| 121 | "Read about Batch 27" |
| 122 | "Fabricated warehouse orders" |
| 123 | "Completed Thieves 1" |
| 124 | "Named dog defiant" |
| 125 | "Named dog depraved" |
| 126 | "Named dog intrigue" |
| 127 | "Named dog seductive" |
| 128 | "Encouraged Foreman's Daughter" |
| 129 | "Removed sandbags" |
| 130 | "Brothel work on" |
| 131 | "Street whore on" |
| 132 | "Bellevue in office" |
| 133 | "Bellevue appointment" |
| 134 | "Mine slavery ended" |
| 135 | "Librarian permission" |
| 136 | "Know about secret passage" |
| 137 | "Moved the bed" |
| 161 | "In plain sight" |
| 162 | "Rescued Aster" |
| 163 | "Latch open" |
| 164 | "Searching thugs" |
| 165 | "Way clear" |
| 166 | "Roaming thugs" |
| 167 | "Thief 3" |
| 168 | "Angry gone" |
| 169 | "No more chances" |
| 170 | "Merc gone" |
| 171 | "Got refugee necklace" |
| 172 | "Stalker attacked" |
| 173 | "Paid guards" |
| 174 | "Street blowjob" |
| 175 | "Chemont stables" |
| 176 | "Helping Sally" |
| 177 | "Romantic fisherman" |
| 178 | "Hurt fisherman" |
| 179 | "Flirty fisherman" |
| 180 | "Boys will be boys" |
| 181 | "Chad turns" |
| 182 | "Enslaved Beth freed" |
| 183 | "Hookton pimp" |
| 184 | "Clue for Dargan" |
| 185 | "Speaking to Tibor" |
| 186 | "Spoke with Tibor" |
| 187 | "Moment of truth" |
| 188 | "Mine barricade broken" |
| 189 | "First slave rallied" |
| 190 | "Yorn escaped" |
| 191 | "Shieldmaiden quest 0" |
| 192 | "Met Gallis" |
| 193 | "Mercenary Quest 1" |
| 194 | "Condolences made" |
| 195 | "Mercenary Quest 2" |
| 196 | "Is mercenary" |
| 197 | "Spoke to Fisher Joe" |
| 198 | "Dealt with Kraken" |
| 199 | "Clue 1 Trevor" |
| 200 | "Clue 2 Trevor" |
| 201 | "Sally's invite" |
| 202 | "Mercenary Quest 3" |
| 203 | "Possessed man killed" |
| 204 | "Possessed man saved" |
| 205 | "Restaurant encounter" |
| 206 | "Kitchen work" |
| 207 | "Kitchen mistake" |
| 208 | "Kitchen pro" |
| 209 | "Plutocrat angry" |
| 210 | "Plutocrat horny" |
| 211 | "Barmaid work" |
| 212 | "Esther wants flowers" |
| 213 | "Refugees moved" |
| 214 | "Unpleasant man kicked" |
| 215 | "Chemont stables 2" |
| 216 | "Know Alex is missing" |
| 217 | "Find Rowena" |
| 218 | "Rowena 'rescued'" |
| 219 | "Audience granted" |
| 220 | "Looking for food" |
| 221 | "Leafy dessert" |
| 222 | "Met Vanessa" |
| 223 | "Vanessa in bedroom" |
| 224 | "Vanessa gives apples" |
| 225 | "Country ambush" |
| 226 | "Find contractor" |
| 227 | "Rose's invitation" |
| 228 | "Chair glows" |
| 229 | "Rose Stage 1" |
| 230 | "Rose Stage 2" |
| 231 | "Unwilling Rose" |
| 232 | "Is a ranger" |
| 233 | "Contractor dealt with" |
| 234 | "Yorns guards killed" |
| 235 | "Charlotte dominated" |
| 236 | "Brother/Sister 2" |
| 237 | "Brother/Sister 3" |
| 238 | "Brother/Sister 4" |
| 239 | "Brother/Sister 5" |
| 240 | "IN CREDITS" |
| 241 | "Lawrence away" |
| 242 | "Lawrence returns" |
| 243 | "Brother/Sister 6" |
| 244 | "Lily not at pond" |
| 245 | "Saw Gilly's captive" |
| 246 | "Met Gilly" |
| 247 | "Bought meds" |
| 248 | "Hut locked" |
| 249 | "Gilly locked up" |
| 250 | "Officer moved" |
| 251 | "Meet Pliny" |
| 252 | "Meet agent" |
| 253 | "Spoke to agent" |
| 254 | "pirateship fucks off" |
| 255 | "Pirates leave" |
| 256 | "Lawrence suspicions" |
| 257 | "Got rid of guard" |
| 258 | "Thief 4" |
| 259 | "Peony 1" |
| 260 | "Temple Invite" |
| 261 | "Peony's guest" |
| 262 | "Rose's guest" |
| 263 | "Lily's guest" |
| 264 | "Met the High Sisters" |
| 265 | "Past the corridor" |
| 266 | "Speak Eastern" |
| 267 | "Esther confronts" |
| 268 | "Esther disappears" |
| 269 | "Lawrence wins" |
| 270 | "Esther wins" |
| 271 | "Nun outfit on" |
| 272 | "Claire is a Sister" |
| 273 | "Rose reappears" |
| 274 | "Dog negated" |
| 275 | "Mountain Lion" |
| 276 | "Pirate vineyard" |
| 277 | "Rathpike variant" |
| 278 | "Guards insulted" |
| 279 | "Peeper tempted" |
| 280 | "Dinner switch" |
| 301 | "Sally's dinner" |
| 302 | "Sally's lover" |
| 303 | "Sally romance failed" |
| 304 | "Investigate lighthouse" |
| 305 | "Blackmail" |
| 306 | "Lighthouse thugs" |
| 307 | "Ransom note read" |
| 308 | "Thug event" |
| 309 | "Prints 1" |
| 310 | "Prints 2" |
| 311 | "Prints 3" |
| 312 | "Prints 4" |
| 313 | "Prints 5" |
| 314 | "Prints 6" |
| 315 | "Found daughter" |
| 316 | "Daughter rescued" |
| 317 | "Lighthouse resolved" |
| 318 | "Thief 5" |
| 319 | "Lion Resolved" |
| 320 | "Lumberjack's clues" |
| 321 | "Met Dorian" |
| 322 | "Dorian analysis 1" |
| 323 | "Roxanne missing" |
| 324 | "Roxanne found" |
| 325 | "Animal outfits" |
| 326 | "Roxanne interferes" |
| 327 | "Met Roxanne" |
| 328 | "Lion solution" |
| 329 | "dinner proc'd" |
| 330 | "Rangers 3" |
| 331 | "Lily 1" |
| 332 | "Tried stable work" |
| 333 | "Refugee necklace spoken" |
| 334 | "Claire is futa" |
| 335 | "Banged a nun" |
| 336 | "Revisit Rose" |
| 337 | "Rose's dungeon opens" |
| 338 | "Rose in dungeon" |
| 339 | "Karland's book read" |
| 340 | "Fairfelt missions finished" |
| 364 | "Karland's errand 2" |
| 365 | "Tricked by Lawrence" |
| 366 | "Aiyana back in lab" |
| 367 | "Grope accepted" |
| 368 | "Rescued waitress" |
| 369 | "Change barmaid outfit" |
| 370 | "Barmaid outfit available" |
| 371 | "Bar lewd possibility" |
| 372 | "Bar lewd locked" |
| 373 | "To be rescued" |
| 374 | "Cockthulu wins" |
| 375 | "Questioning elders" |
| 376 | "Gravekeeper OK" |
| 377 | "Brother interacted" |
| 378 | "Shotaghost engaged" |
| 379 | "Aidan freed" |
| 380 | "Cockthulu loses" |
| 381 | "Bed made" |
| 382 | "Bed is unmade" |
| 383 | "Got dressed" |
| 384 | "Ate food" |
| 385 | "Mother downstairs" |
| 386 | "Item Blurb" |
| 387 | "Get the pouch" |
| 388 | "Kindling in house" |
| 389 | "Bring in kindling" |
| 390 | "Clothes on table" |
| 391 | "Revived the youth" |
| 392 | "Spoke to grim refugee" |
| 393 | "Monster warning" |
| 394 | "Elder interacted" |
| 395 | "Elder permit" |
| 396 | "Trauma gypsy" |
| 397 | "DOMINANT Sister" |
| 398 | "SUBMISSIVE Sister" |
| 399 | "PROLOGUE COMPLETE" |
| 400 | "MASTER SWITCH RELEASE" |
| 401 | "Breadcrumb yuri" |
| 402 | "Wolves at the door" |
| 403 | "Dorian in outpost" |
| 404 | "Wolf outfit unlocked" |
| 405 | "Wolf solution" |
| 406 | "Wolves dealt with" |
| 407 | "Ranger 3" |
| 408 | "Brugginwood warning" |
| 409 | "Lily 2" |
| 410 | "Lily 3" |
| 411 | "Rose 5" |
| 412 | "Talin in cave" |
| 413 | "Find Talin" |
| 414 | "Talin at Lodge front" |
| 415 | "Find Dorian for bear" |
| 416 | "Dorian analysis 2" |
| 417 | "Get bear solution" |
| 418 | "Confront poachers" |
| 419 | "Poachers distracted" |
| 420 | "Bear outfit unlocked" |
| 421 | "Bear resolved" |
| 422 | "Cabaret work enabled" |
| 423 | "Wearing cabaret outfit" |
| 424 | "Set down box" |
| 425 | "Box open" |
| 426 | "The chase" |
| 427 | "Bet big" |
| 428 | "Bet small" |
| 429 | "1. Fool" |
| 430 | "2. Lover" |
| 431 | "3. Knave" |
| 432 | "4. Hermit" |
| 433 | "5. Warrior" |
| 434 | "6. Ruler" |
| 435 | "Inquire about Lasson" |
| 436 | "Wanna buy a barn?" |
| 437 | "Dead thief scene" |
| 438 | "Woman's corpse" |
| 439 | "Disabled lock" |
| 440 | "Idling" |
| 441 | "Pub basement unlocked" |
| 442 | "Workers fantasy" |
| 443 | "C.B.R. Owned" |
| 444 | "bought Gale" |
| 445 | "bought Thunder" |
| 446 | "bought Brutus" |
| 447 | "Debtor encounter" |
| 448 | "Seaside House Liberated" |
| 449 | "1st Day Meat Pit over" |
| 450 | "Meat Pit A" |
| 451 | "Meat Pit B" |
| 452 | "Runaways helped" |
| 453 | "Did not take runaways money" |
| 454 | "Met Isobelle" |
| 455 | "Bullpen intro" |
| 456 | "Cabaret Goldroom" |
| 457 | "Urchin hideout" |
| 458 | "Cleaning job get" |
| 459 | "Cleaning job lost" |
| 460 | "Dogs walked" |
| 461 | "Boat rowed" |
| 462 | "Cottage reached" |
| 463 | "Fat Jack KO'd" |
| 464 | "Hole in the ground" |
| 465 | "Met Gale before" |
| 466 | "Beth leaves a free woman" |
| 467 | "Visited Seaside Cottage" |
| 468 | "Forbidden cave solved" |
| 469 | "Belisaros met" |
| 470 | "Inn asked" |
| 471 | "On the trail" |
| 472 | "Inside Nachali lair" |
| 473 | "Rose on the harvest" |
| 474 | "Nachali appears" |
| 475 | "Nachali disappears" |
| 476 | "Nachali appears 2" |
| 477 | "Nachali disappears 2" |
| 478 | "Brew the potion" |
| 479 | "The Chase Begins" |
| 480 | "Nachali appears 3" |
| 481 | "Nachali falls" |
| 482 | "Path opens" |
| 483 | "Confront the Library" |
| 484 | "Alchemy Experiments Unlocked" |
| 485 | "Trapper: Manticore" |
| 486 | "Trapper: Dreadfly" |
| 487 | "Pirate stuffed" |
| 488 | "blackblood" |
| 489 | "Old Girl" |
| 490 | "Obs Report" |
| 491 | "Found dead merc" |
| 492 | "Dead and gone" |
| 493 | "Belisaros's Grave" |
| 494 | "Met Slayer" |
| 495 | "Its Goblins" |
| 496 | "Dreadfly explanation" |
| 497 | "Food consumed" |
| 498 | "Inventory restored" |
| 499 | "VALOS SWITCH RELEASED" |
| 500 | "RATHPIKE SWITCH RELEASED" |
| 521 | "Breakout" |
| 522 | "Weapons free" |
| 523 | "Human trafficking resolved" |
| 524 | "Contemplation" |
| 525 | "Bjorn in casino" |
| 526 | "Leon denied" |
| 527 | "Met Old Red" |
| 528 | "Dockhouse open" |
| 529 | "Bjorn enters" |
| 530 | "Aslaug enters" |
| 531 | "Shieldmaiden 2" |
| 532 | "get Aslaug's armor" |
| 533 | "Get the horn" |
| 534 | "Shieldmaiden Wear" |
| 535 | "Tahlia Active" |
| 536 | "GoW Lily2" |
| 537 | "GoW Lily3" |
| 538 | "Nymph appears" |
| 539 | "GoW Lily4" |
| 540 | "Gow Rose2" |
| 541 | "Lily MGS" |
| 542 | "GoW Rose3" |
| 543 | "GoW Rose4" |
| 544 | "Rose MGS" |
| 545 | "Isobelle level1" |
| 546 | "Isobelle level3" |
| 547 | "Isobelle level2" |
| 548 | "Isobelle level4" |
| 549 | "Isobelle level5" |
| 550 | "Isobelle level6" |
| 551 | "Isobelle level7" |
| 552 | "Isobelle level8" |
| 553 | "Isobelle is beastwife" |
| 554 | "Isobelle has piercings" |
| 555 | "Reunited with Beth" |
| 556 | "Robbed" |
| 557 | "Goblin #2" |
| 558 | "Spoke to wormgirl" |
| 559 | "wormies left" |
| 560 | "tracks" |
| 561 | "Found Karland" |
| 562 | "Found Camp" |
| 563 | "Bertrand 2" |
| 564 | "Rescued Louis" |
| 565 | "Therese in study" |
| 566 | "tannery investigation" |
| 567 | "clothes clue" |
| 568 | "Rangers sent" |
| 569 | "Leyton outside" |
| 570 | "Find rangers" |
| 571 | "Grove open" |
| 572 | "Rangers ded" |
| 573 | "Louis runs off" |
| 574 | "werewolf clue1" |
| 575 | "werewolf clue2" |
| 576 | "Nymph gone" |
| 577 | "Treat wolfsbane" |
| 578 | "Prepare campfires" |
| 579 | "Werewolf active" |
| 580 | "Louis out" |
| 581 | "Werewolf bait" |
| 582 | "Werewolf fire" |
| 583 | "Speak to Louis" |
| 584 | "Louis approval" |
| 585 | "Werewolf transformed" |
| 586 | "Rain thugs defeated" |
| 587 | "goblin2 begins" |
| 588 | "investigate graveyard" |
| 589 | "seek goblin clues" |
| 590 | "bones recovered" |
| 591 | "slayer hiding" |
| 592 | "backstab skill on" |
| 593 | "slayer in cave" |
| 594 | "slayer leaves cave" |
| 595 | "final cave" |
| 596 | "goblin cave murdered" |
| 597 | "goblin #1 complete" |
| 598 | "Badweather CountStart" |
| 599 | "Bad Weather Warning" |
| 600 | "RAINING (OUTER VALOS)" |
| 601 | "DISABLE GALLERY" |
| 602 | "Sandworm cave found" |
| 603 | "3RD TRIMESTER (VALOS)" |
| 604 | "2ND TRIMESTER" |
| 605 | "OPTION: PREG?" |
| 606 | "Valos1Pregnancy" |
| 607 | "run wormies run" |
| 608 | "sandworm dam sabotaged" |
| 609 | "staying at Adelaide" |
| 610 | "BethxGale" |
| 611 | "Bakerfamily in inn" |
| 612 | "hidden sandworm" |
| 613 | "omega stays" |
| 614 | "what does it all mean?" |
| 615 | "what does it all mean2?" |
| 616 | "sandworm cave flood" |
| 617 | "the proposal (beth)" |
| 618 | "yana x claire sitting in a tree" |
| 619 | "tackling fairies" |
| 620 | "fairies resolved" |
| 621 | "lamp observation (Fairy)" |
| 622 | "fairiez" |
| 623 | "festival during" |
| 624 | "festival active" |
| 625 | "fiddlechime obedient" |
| 626 | "renovations (hotel)" |
| 627 | "alligator1" |
| 628 | "alligator2" |
| 629 | "alligator3" |
| 630 | "alligator4" |
| 631 | "alligator5" |
| 632 | "alligator6" |
| 633 | "lizardgirl outfit unlocked" |
| 634 | "alligator 7" |
| 635 | "alligator resolved" |
| 636 | "urchin trigger" |
| 637 | "urchin scene" |
| 638 | "urchins passed" |
| 639 | "fucked by urchins" |
| 640 | "harvest fest fin." |
| 641 | "Meetyourmaker(Dom)" |
| 642 | "Meetyourmaker(Sub)" |
| 643 | "Thugs slattern talked" |
| 644 | "thug patrol over" |
| 645 | "ValosChild-RangerAdopted" |
| 646 | "ValosChild-Sold" |
| 647 | "ValosChild-Fostered" |
| 648 | "ValosChild-ClaimedRanch" |
| 649 | "ValosLabour" |
| 650 | "VBabyDelivered" |
| 651 | "ValosChild Born" |
| 652 | "GenevieveVolunteer" |
| 653 | "Is Nurse" |
| 654 | "Nurse task1" |
| 655 | "Nurse task2" |
| 656 | "Nurse task3" |
| 657 | "Jillian encounter" |
| 658 | "Jillian's suspicions" |
| 659 | "Nightclinic" |
| 660 | "Basement open" |
| 661 | "Chest01-InnerValos" |
| 662 | "Ore01-BootleggersTunnel" |
| 663 | "Tree01-FarmersCountry" |
| 664 | "BrambleRose-1" |
| 665 | "BrambleRose-2" |
| 666 | "BrambleRose-3" |
| 667 | "BrambleRose-4" |
| 668 | "AmberLily-1" |
| 669 | "AmberLily-2" |
| 670 | "AmberLily-3" |
| 671 | "AmberLily-4" |
| 672 | "AmberLily-5" |
| 673 | "Wolfsbane-1" |
| 674 | "Wolfsbane-2" |
| 675 | "Wolfsbane-3" |
| 676 | "Wolfsbane-4" |
| 677 | "Wolfsbane-5" |
| 678 | "Chest02-OuterValos" |
| 679 | "RathOre01-Beach" |
| 680 | "RathOre02-Beach" |
| 681 | "boxlaid" |
| 682 | "chimera moved" |
| 683 | "genevieve decision" |
| 684 | "Revilliers doomed" |
| 685 | "metChloe" |
| 686 | "metMarj" |
| 687 | "metFarrow" |
| 688 | "sortedPaperwork" |
| 689 | "metTravs" |
| 690 | "JillianBroken" |
| 691 | "sidewithRevs" |
| 692 | "wimp deployed" |
| 693 | "kindling removed" |
| 694 | "spoke to knight" |
| 695 | "stella spoken" |
| 696 | "spoke to prioress" |
| 697 | "spoke to Charlotte (Rivermont)" |
| 698 | "bertrand backstep" |
| 699 | "blockade cleared" |
| 700 | "stashmessage" |
| 721 | "Leon hidden" |
| 722 | "Leon found" |
| 723 | "Tubbs route" |
| 724 | "Tubbs route 2" |
| 725 | "deepthroated once" |
| 726 | "hamlet pigs active" |
| 727 | "knight free" |
| 728 | "Rainier breakout" |
| 729 | "EARLY RivermontSave" |
| 730 | "Castle Escape" |
| 731 | "Mother in Rivermont" |
| 732 | "playing dead" |
| 733 | "Stella in keep" |
| 734 | "stella saving" |
| 735 | "stella saving 2" |
| 736 | "drawbridge up" |
| 737 | "boat unavailable" |
| 738 | "Mummy rescued" |
| 739 | "Marie rescued" |
| 740 | "Stella scene" |
| 741 | "Leon back to Charlotte (Rivermont)" |
| 742 | "Prioress's Weapon" |
| 743 | "debris moved" |
| 744 | "pig discovered" |
| 745 | "halfdrowned rescued" |
| 746 | "got into the castle" |
| 747 | "pigboss encountered (Rainier)" |
| 748 | "End of Rivermont" |
| 749 | "Rivermont Route" |
| 750 | "Jeremus quest" |
| 751 | "Charlotte rivermont quest" |
| 752 | "LATE Rivermont escape" |
| 753 | "Met Phantasm" |
| 754 | "SoF: Stone Oak" |
| 755 | "Rangers: Wounded front" |
| 756 | "Rangers: Rescue Talin" |
| 757 | "injured ranger cleared" |
| 758 | "rangers in lake" |
| 759 | "find Talin" |
| 760 | "Roxanne stranded" |
| 761 | "wolfpack" |
| 762 | "bearskin removed" |
| 763 | "Maude left" |
| 764 | "Talin rescued" |
| 765 | "Dorian dead" |
| 766 | "quarreling pigmen met" |
| 767 | "Mia at Wine Country" |
| 768 | "Stone Oak resolved" |
| 769 | "Rose confrontation" |
| 770 | "Lily confrontation" |
| 771 | "Peony by the pier" |
| 772 | "Dorian's grave visited" |
| 773 | "Roxanne at tunnels" |
| 774 | "monkey business" |
| 775 | "monkeys resolved" |
| 776 | "rox distracts tiger" |
| 777 | "monke deployed" |
| 778 | "monke traps" |
| 779 | "monkey traps revealed" |
| 780 | "tunnels with rox" |
| 781 | "searching for mother" |
| 782 | "kingdom calls" |
| 783 | "fine wine req" |
| 784 | "faelarks" |
| 785 | "empyrean visit" |
| 786 | "nightmare" |
| 787 | "nightmare seen" |
| 788 | "dreaming begins" |
| 789 | "door opens" |
| 790 | "mum appears" |
| 791 | "choices" |
| 792 | "quake" |
| 793 | "rivermont memory" |
| 794 | "fairylight" |
| 795 | "wolves appear" |
| 796 | "death by wolf" |
| 797 | "mom in shock" |
| 798 | "dream 1 resolved" |
| 799 | "dream 2 resolved" |
| 800 | "mother gets up" |
| 801 | "cell sequence ends" |
| 802 | "mother's conclusion" |
| 803 | "dream 3 resolved" |
| 804 | "Nightmare Ended" |
| 805 | "speak to contractor" |
| 806 | "renovations done" |
| 807 | "bellevue renovated" |
| 808 | "charlotte whored out" |
| 809 | "charlotte's family turn'd" |
| 810 | "moving chairs" |
| 811 | "chairs moved" |
| 812 | "bath over" |
| 813 | "bellevue's invite" |
| 814 | "Leon seduced" |
| 815 | "claire x bellevue on" |
| 816 | "Cabaret PurpleFloor" |
| 817 | "Lawrence Slave BG" |
| 818 | "ValosChild-ClaimedMaison" |
| 819 | "Working Gold Floor" |
| 820 | "Wearing Gold Floor outfit" |
| 821 | "Gold Floor 1" |
| 822 | "Gold Floor 2" |
| 823 | "Gold Floor 3" |
| 824 | "Grave of the Fireflies" |
| 825 | "marie w/ mum" |
| 826 | "naptime over" |
| 827 | "mum in Ranch" |
| 828 | "mum in Maison" |
| 829 | "moved out of tannery" |
| 830 | "taming the shrew" |
| 831 | "spoke to Corentin" |
| 832 | "spoke to Eleanor" |
| 833 | "High Sister chosen" |
| 834 | "Lily tames shrew" |
| 835 | "Rose tames shrew" |
| 836 | "LilyShrew:Futa" |
| 837 | "LilyShrew:Dildo" |
| 838 | "RoseShrew:Futa" |
| 839 | "RoseShrew:MiaFuta" |
| 840 | "ShrewEnding" |
| 841 | "ShamanDeath#1" |
| 842 | "End-CorentinDom" |
| 843 | "End-EleanorDom/Boywife" |
| 844 | "End-EleanorDom/Cuckold" |
| 845 | "Elsie in room" |
| 846 | "These Old Bones" |
| 847 | "Rangers in dead of woods" |
| 848 | "sinnsith1 witnessed" |
| 849 | "sinnsith2 witnessed" |
| 850 | "sinnsith active" |
| 851 | "maude appears" |
| 852 | "flowers up" |
| 853 | "leon out" |
| 854 | "suite visit" |
| 855 | "no suite for charlotte" |
| 856 | "suite for charlotte" |
| 857 | "UtT ended" |
| 858 | "dinnertime" |
| 859 | "dinnertime over" |
| 860 | "SUCCUBINE PERSUASION" |
| 861 | "Tree03-WhiteHart" |
| 862 | "Tree04-WhiteHart" |
| 901 | "Charlotte is Bellevue's" |
| 902 | "Oyakodon" |
| 903 | "Charlotte SP'd" |
| 904 | "sapphic Charlotte" |
| 905 | "Leon lover" |
| 906 | "evelyn heritage" |
| 907 | "evelyn spied on" |
| 908 | "ranch lawn'd" |
| 909 | "evelyn proposal" |
| 910 | "abbess left" |
| 911 | "clash of faiths" |
| 912 | "peony left" |
| 913 | "spoke to mia" |
| 914 | "abbey-mauso exit" |
| 915 | "clerics leave for Port" |
| 916 | "ulias" |
| 917 | "ulias passage" |
| 918 | "karland library" |
| 919 | "caria meet" |
| 920 | "caria suspicions" |
| 921 | "caria down" |
| 922 | "caria transformed" |
| 923 | "lock open" |
| 924 | "library resolved" |
| 925 | "chest 1 opened" |
| 926 | "chest 2 opened" |
| 927 | "chest 3 opened" |
| 928 | "catch!" |
| 929 | "head librarian cured" |
| 930 | "ulias mission" |
| 931 | "ulias mission 2" |
| 932 | "bookhint1" |
| 933 | "bookhint2" |
| 934 | "ulias mission 3" |
| 935 | "satyr out" |
| 936 | "satyr driven away" |
| 937 | "satyrs active" |
| 938 | "a way inside" |
| 939 | "mia/claire fell" |
| 940 | "clash resolved" |
| 941 | "rescue delay" |
| 942 | "schism" |
| 943 | "redmist" |
| 944 | "kill a god 1" |
| 945 | "kill a god 2" |
| 946 | "kill a god 3" |
| 947 | "kill a god 4" |
| 948 | "weird statue" |
| 949 | "cleaned" |
| 950 | "kill a god 5" |
| 951 | "kill a god 6" |
| 952 | "kill a god 7" |
| 953 | "bruggin summoned" |
| 954 | "basilisk active" |
| 955 | "at least one obelisk" |
| 956 | "holy water" |
| 957 | "obelisk 1 purified" |
| 958 | "victory over maude" |
| 959 | "obelisk 2 purified" |
| 960 | "obelisk 3 purified" |
| 961 | "bruggin up" |
| 962 | "bruggin full" |
| 963 | "maude killed" |
| 964 | "SpeakWithAnimals" |
| 965 | "RANGERS COMPLETE" |
| 966 | "Beth level1" |
| 967 | "Beth level2" |
| 968 | "Beth level3" |
| 969 | "Beth level4" |
| 970 | "Beth level5" |
| 971 | "Beth level6" |
| 972 | "Beth level7" |
| 973 | "Beth level8" |
| 974 | "Siding with Lily" |
| 975 | "Siding with Rose" |
| 976 | "hotel escape clue" |
| 977 | "hotel escaped" |
| 978 | "hotel invaded" |
| 979 | "Antiquarian setup" |
| 980 | "SIEGE OVER" |
| 981 | "GroundAttackPrepA" |
| 982 | "GroundAttackUtilityA" |
| 983 | "GroundAttackA" |
| 984 | "GroundAttackPrepB" |
| 985 | "GroundAttackUtilityB" |
| 986 | "GroundAttackB" |
| 987 | "GroundAttackPrepC" |
| 988 | "GroundAttackUtilityC" |
| 989 | "GroundAttackC" |
| 990 | "BLADDER SWITCH" |
| 995 | "Lady Luck Intro" |
| 996 | "ALCOHOL COOLDOWN" |
| 997 | "Intro: Pigs" |
| 998 | "Intro: Parents" |
| 999 | "Intro: Dad Away" |
| 1000 | "DIRECTIONS OFF" |
| 1001 | "Bet hearts" |
| 1002 | "Bet diamonds" |
| 1003 | "Bet clubs" |
| 1004 | "Bet spades" |
| 1005 | "In sandstorm shelter" |
| 1006 | "Peony is fine" |
| 1007 | "Peony's tree" |
| 1008 | "After Peony femdom" |
| 1009 | "Deployed against Peony" |
| 1010 | "Peony reversal" |
| 1011 | "Peony reversal fin" |
| 1012 | "Isander active" |
| 1013 | "Isander is HERE!" |
| 1014 | "beer 1" |
| 1015 | "beer 2" |
| 1016 | "beer 3" |
| 1017 | "bought beer" |
| 1018 | "Isander's weapon" |
| 1019 | "Lamp shatters" |
| 1020 | "moonshine" |
| 1021 | "no drinks for Isander" |
| 1022 | "bounty hunters" |
| 1023 | "bounty hunted" |
| 1024 | "Isander encountered" |
| 1025 | "Gypsy totem lore" |
| 1026 | "Rose turncoat" |
| 1027 | "Gate gypsy moved" |
| 1028 | "Ulias Final" |
| 1029 | "Torture philosophy" |
| 1030 | "I want a face" |
| 1031 | "face taken" |
| 1032 | "face given" |
| 1033 | "driome released" |
| 1034 | "andumas unlocked" |
| 1035 | "mid switch" |
| 1036 | "undercrypt gate" |
| 1037 | "thurible unloaded" |
| 1038 | "thurible taken" |
| 1039 | "Valos Rises" |
| 1040 | "Bertrand away" |
| 1041 | "Skulduggery01-CupTrotter" |
| 1042 | "Skulduggery02-Hotel" |
| 1043 | "Skulduggery03-Wayside" |
| 1044 | "Skulduggery04-Brothel" |
| 1045 | "Skulduggery05-Slattern" |
| 1046 | "Skulduggery06-Casino" |
| 1047 | "RathOre03-Forsaken" |
| 1048 | "RathOre04-Forsaken" |
| 1049 | "RathOre05-Forsaken" |
| 1050 | "Chest03-RathWest" |
| 1051 | "Chest04-TheWash" |
| 1052 | "PICKPOCKET INFO" |
| 1053 | "GUARANTEED PREG" |
| 1054 | "ALCHEMY BASES" |
| 1055 | "Open da windows!" |
| 1056 | "SCAVENGE INFO" |
| 1057 | "FORAGING INFO" |
| 1058 | "Smugglers' Tunnel Hazard" |
| 1059 | "Whores' End Hazard" |
| 1060 | "UNHEALTHY ENVIRON WARNING" |
| 1061 | "Camp: Badlands" |
| 1062 | "Camping Info" |
| 1063 | "Camp: Brugginwood" |
| 1064 | "Gem Auction: Valos CD" |
| 1065 | "Gem Auction: Rathpike CD" |
| 1066 | "ValosOre01-PoachTunnel" |
| 1067 | "ValosOre02-PoachTunnel" |
| 1068 | "ValosOre03-Libertine" |
| 1069 | "ValosOre04-Libertine" |
| 1070 | "Book Benefit: Latin" |
| 1071 | "Knowledge: GloryDead" |
| 1074 | "Book Benefit: EvilClass" |
| 1075 | "Book Benefit: Karland" |
| 1076 | "Book Benefit: Carnal" |
| 1077 | "Book Benefit: Killers" |
| 1078 | "Book Benefit: Glory" |
| 1079 | "Book Benefit: Pluto" |
| 1080 | "Book Benefit: Maid" |
| 1081 | "rain event done once" |
| 1082 | "cove accessed" |
| 1083 | "Abbey Intro" |
| 1084 | "DeerGirl Intro" |
| 1085 | "greet Savord" |
| 1086 | "Trissengrad Silver Lore" |
| 1087 | "Beth is beastwife" |
| 1088 | "Beth has piercings" |
| 1089 | "DIFFICULTY: EASY" |
| 1093 | "Sleep/Paupers Revisit" |
| 1094 | "Sleep/Paupers Scared" |
| 1095 | "Pauper "D" version unlocked" |
| 1096 | "Dining: Fish Fillets" |
| 1097 | "Dining: Mom's Stew" |
| 1098 | "Dining: Claire's Toast" |
| 1099 | "Dining: Saveur" |
| 1100 | "Claire: Cannibal!" |

#### Collection/Exploration Flags

| ID | Name |
|---|---|
| 138 | "Evidence A" |
| 139 | "Evidence B" |
| 140 | "Evidence C" |
| 661 | "Chest01-InnerValos" |
| 662 | "Ore01-BootleggersTunnel" |
| 663 | "Tree01-FarmersCountry" |
| 664 | "BrambleRose-1" |
| 665 | "BrambleRose-2" |
| 666 | "BrambleRose-3" |
| 667 | "BrambleRose-4" |
| 668 | "AmberLily-1" |
| 669 | "AmberLily-2" |
| 670 | "AmberLily-3" |
| 671 | "AmberLily-4" |
| 672 | "AmberLily-5" |
| 673 | "Wolfsbane-1" |
| 674 | "Wolfsbane-2" |
| 675 | "Wolfsbane-3" |
| 676 | "Wolfsbane-4" |
| 677 | "Wolfsbane-5" |
| 678 | "Chest02-OuterValos" |
| 679 | "RathOre01-Beach" |
| 680 | "RathOre02-Beach" |
| 925 | "chest 1 opened" |
| 926 | "chest 2 opened" |
| 927 | "chest 3 opened" |

#### Knowledge/Book Benefit Flags

| ID | Name |
|---|---|
| 1070 | "Book Benefit: Latin" |
| 1071 | "Knowledge: GloryDead" |
| 1074 | "Book Benefit: EvilClass" |
| 1075 | "Book Benefit: Karland" |
| 1076 | "Book Benefit: Carnal" |
| 1077 | "Book Benefit: Killers" |
| 1078 | "Book Benefit: Glory" |
| 1079 | "Book Benefit: Pluto" |
| 1080 | "Book Benefit: Maid" |

#### Area/Location Flags

| ID | Name |
|---|---|
| 41 | "IN GALLERY" |
| 240 | "IN CREDITS" |
| 600 | "RAINING (OUTER VALOS)" |
| 601 | "DISABLE GALLERY" |
| 603 | "3RD TRIMESTER (VALOS)" |
| 604 | "2ND TRIMESTER" |

#### Relationship Flags

| ID | Name |
|---|---|
| 302 | "Sally's lover" |
| 303 | "Sally romance failed" |
| 610 | "BethxGale" |
| 904 | "sapphic Charlotte" |
| 905 | "Leon lover" |
| 974 | "Siding with Lily" |
| 975 | "Siding with Rose" |

#### Master Gate Switches

| ID | Name |
|---|---|
| 400 | "MASTER SWITCH RELEASE" |
| 499 | "VALOS SWITCH RELEASED" |
| 500 | "RATHPIKE SWITCH RELEASED" |

---

## 5. Variables

**Total**: 83 variables (index 1–83)  
**Named**: 80 variables  
**Unused/Empty**: 3 variables (index 78, 79, 83)

Variable index 0 is always empty (placeholder for 1-based RPG Maker indexing).

### 5.1 Complete Inventory

| ID | Name | Category |
|---|---|---|
| 1 | "View objectives" | UI State |
| 2 | "Claire's Defiance" | **Core Stat** |
| 3 | "Claire's Depravity" | **Core Stat** |
| 4 | "Claire's Hunger" | Survival Stat |
| 5 | "Silver amount" | Currency |
| 6 | "Claire's Seduction" | **Core Stat** |
| 7 | "Claire's Intrigue" | **Core Stat** |
| 8 | "Coordi 1" | Outfit/Coordination |
| 9 | "Coordi 2" | Outfit/Coordination |
| 10 | "Coordi 3" | Outfit/Coordination |
| 11 | "Claire's Energy" | Survival Stat |
| 12 | "BakerS: Leon Affect." | Affection Tracker |
| 13 | "Lawrence's Affection" | Affection Tracker |
| 14 | "Rooms cleaned" | Quest Counter |
| 15 | "Unpleasant man tension" | Quest Counter |
| 16 | "Mox's approval" | Affection Tracker |
| 17 | "Hopeful slaves" | Progress Tracker |
| 18 | "Drinks on tray" | Progress Tracker |
| 19 | "Bar patron libido" | Progress Tracker |
| 20 | "Vanessa affection" | Affection Tracker |
| 21 | "Esther's dominance" | Affection Tracker |
| 22 | "Random Book" | RNG |
| 23 | "Lily's affection" | Affection Tracker |
| 24 | "Monster Tokens" | Currency/Tokens |
| 25 | "Caught mushrooms" | Collectible Counter |
| 26 | "Number of tigerlilies" | Collectible Counter |
| 27 | "Haunting clue" | Quest Counter |
| 28 | "Cabaret stage" | Progress Tracker |
| 29 | "Money Randomizer" | RNG |
| 30 | "Diceroll" | RNG |
| 31 | "Cards" | Card Game State |
| 32 | "No. of Beasts" | Progress Counter |
| 33 | "Loot Randomizer" | RNG |
| 34 | "Rainstorm Chance" | RNG |
| 35 | "Isobelle Fatigue" | NPC State |
| 36 | "Isobelle Stepcounter" | NPC State |
| 37 | "Outposts visited" | Progress Counter |
| 38 | "Shiv sharpness" | Item State |
| 39 | "Alchemy Components" | Inventory Counter |
| 40 | "Rivermont Days" | Day Counter |
| 41 | "Leyton Clues" | Quest Counter |
| 42 | "Wolfsbane Counter" | Quest Counter |
| 43 | "Campfire Counter" | Quest Counter |
| 44 | "Wolf Fire Counter" | Quest Counter |
| 45 | "Badweather RESET" | Weather Control |
| 46 | "BakerS: ?" | Unknown |
| 47 | "BakerS: Corruption" | Progress Tracker |
| 48 | "BakerS: Charlotte's Affect." | Affection Tracker |
| 49 | "Preg Randomizer" | RNG |
| 50 | "1/4 Success Lockpick" | Skill Check |
| 51 | "1/2 Success Lockpick" | Skill Check |
| 52 | "Tree Stump Danger" | Quest Counter |
| 53 | "Beth Fatigue" | NPC State |
| 54 | "Beth Stepcounter" | NPC State |
| 55 | "Pregnancy CD Timer" | Cooldown Timer |
| 56 | "V-RanchChildGrowth" | Pregnancy Growth |
| 57 | "V-RangerChildGrowth" | Pregnancy Growth |
| 58 | "V-BrabannoisChildGrowth" | Pregnancy Growth |
| 59 | "Townsfolk spoken to out of 6" | Progress Counter |
| 60 | "Stella Romance" | Affection Tracker |
| 61 | "hyena trail" | Quest Counter |
| 62 | "sold large gem counter" | Economy Counter |
| 63 | "dream steps" | Progress Counter |
| 64 | "gold floor view" | Progress Counter |
| 65 | "gold floor progress" | Progress Counter |
| 66 | "chatting with mum" | Progress Counter |
| 67 | "Evie Fatigue" | NPC State |
| 68 | "Evie Stepcounter" | NPC State |
| 69 | "obelisks purified" | Quest Counter |
| 70 | "eostre witnessed" | Event Flag |
| 71 | "Isander's Respect" | Affection Tracker |
| 72 | "Number of item" | Inventory Counter |
| 73 | "Camping rest" | Survival Stat |
| 74 | "Claire's Max. Hunger" | Max Stat |
| 75 | "Claire's Max. Energy" | Max Stat |
| 76 | "gold amount" | Currency |
| 80 | "Card draw" | Card Game RNG |
| 81 | "FAME" | **Core Stat** |
| 82 | "DRUNKNESS" | Status Effect |
| 83 | "BOWELS/BLADDER" | Survival/Meter |

### 5.2 Variable Categories

#### Core Stats (Player Character)

| ID | Name | RPG Maker Param Index |
|---|---|---|
| 2 | "Claire's Defiance" | 2 (Attack renamed) |
| 3 | "Claire's Depravity" | 3 (Defense renamed) |
| 6 | "Claire's Seduction" | 7 (Luck renamed) |
| 7 | "Claire's Intrigue" | 6 (Agility renamed) |
| 81 | "FAME" | — (custom) |

#### Survival Stats

| ID | Name |
|---|---|
| 4 | "Claire's Hunger" |
| 11 | "Claire's Energy" |
| 73 | "Camping rest" |
| 74 | "Claire's Max. Hunger" |
| 75 | "Claire's Max. Energy" |
| 82 | "DRUNKNESS" |
| 83 | "BOWELS/BLADDER" |

#### Currency

| ID | Name |
|---|---|
| 5 | "Silver amount" |
| 24 | "Monster Tokens" |
| 76 | "gold amount" |

#### Affection Trackers

| ID | Name |
|---|---|
| 12 | "BakerS: Leon Affect." |
| 13 | "Lawrence's Affection" |
| 16 | "Mox's approval" |
| 20 | "Vanessa affection" |
| 21 | "Esther's dominance" |
| 23 | "Lily's affection" |
| 48 | "BakerS: Charlotte's Affect." |
| 60 | "Stella Romance" |
| 71 | "Isander's Respect" |

#### RNG / Random Values

| ID | Name |
|---|---|
| 22 | "Random Book" |
| 29 | "Money Randomizer" |
| 30 | "Diceroll" |
| 31 | "Cards" |
| 33 | "Loot Randomizer" |
| 34 | "Rainstorm Chance" |
| 49 | "Preg Randomizer" |
| 80 | "Card draw" |

---

## 6. Stat System (terms.params)

RPG Maker defines 10 base parameters (indices 0–9). This game **redefines** several to custom stats.

### 6.1 Parameter Mapping

| Index | Default RPG Maker | This Game's Name | Purpose |
|---|---|---|---|
| 0 | Max HP | "MAX. HP" | Hit Points cap |
| 1 | Max MP | "MAX. EP" | Energy Points cap (renamed from Magic Points) |
| 2 | Attack | "Defiance" | **Primary combat/social stat** |
| 3 | Defense | "Depravity" | **Primary combat/social stat** |
| 4 | M.Attack | "M. Attack" | Magic attack (kept default) |
| 5 | M.Defense | "M. Defense" | Magic defense (kept default) |
| 6 | Agility | "Intrigue" | **Social/exploration stat** |
| 7 | Luck | "Seduction" | **Social/charm stat** |
| 8 | Accuracy | "Accuracy" | Hit chance (kept default) |
| 9 | Evasiveness | "Evasiveness" | Dodge chance (kept default) |

### 6.2 Transpiler Relevance

When map events use **Conditional Branch (code 111)** with **type 4 (Actor Parameter)**:

```
Conditional Branch: Script: $gameActors.actor(1).param(2) >= 10
```

The parameter index (2) maps to "Defiance" via `terms.params[2]`. The transpiler should resolve:

```
if claire_defiance >= 10:
```

---

## 7. Basic Terms (terms.basic)

| Index | Full Name | Abbreviated |
|---|---|---|
| 0 | "Level" | "Lvl." |
| 2 | "Hunger Points" | "HP" |
| 4 | "Energy Points" | "EP" |
| 6 | "Fame" | "Fame" |
| 8 | "EXP" | "EXP" |

**Key insight**: RPG Maker defaults (HP = Hit Points, MP = Magic Points, TP = Tactical Points) are renamed to survival-themed terms.

---

## 8. Terms Commands

| Index | Command |
|---|---|
| 0 | "Fight" |
| 1 | "Escape" |
| 2 | "Attack" |
| 3 | "Guard" |
| 4 | "Inventory" |
| 5 | "Skill" |
| 6 | "Equip" |
| 7 | "Status" |
| 8 | "Formation" |
| 9 | "Save" |
| 10 | "Quit" |
| 11 | "Options" |
| 12 | "Food Only" |
| 13 | "Books Only" |
| 14 | "Quest Only" |
| 15 | "Equip" |
| 16 | "Optimize" |
| 17 | "Clear" |
| 18 | "New Game" |
| 19 | "Load Game" |
| 20 | (null) |
| 21 | "Back To Title" |
| 22 | "Cancel" |
| 23 | (null) |
| 24 | "Buy" |
| 25 | "Sell" |

---

## 9. Terms Messages

| Key | Template |
|---|---|
| `actionFailure` | "There was no effect on %1!" |
| `actorDamage` | "%1 took %2 damage!" |
| `actorDrain` | "%1 was drained of %2 %3!" |
| `actorGain` | "%1 gained %2 %3!" |
| `actorLoss` | "%1 lost %2 %3!" |
| `actorNoDamage` | "%1 took no damage!" |
| `actorNoHit` | "Miss! %1 took no damage!" |
| `actorRecovery` | "%1 recovered %2 %3!" |
| `alwaysDash` | "Always Dash" |
| `bgmVolume` | "BGM Volume" |
| `bgsVolume` | "BGS Volume" |
| `buffAdd` | "%1's %2 went up!" |
| `buffRemove` | "%1's %2 returned to normal!" |
| `commandRemember` | "Command Remember" |
| `counterAttack` | "%1 counterattacked!" |
| `criticalToActor` | "A painful blow!!" |
| `criticalToEnemy` | "An excellent hit!!" |
| `debuffAdd` | "%1's %2 went down!" |
| `defeat` | "%1 was defeated." |
| `emerge` | "%1 emerged!" |
| `enemyDamage` | "%1 took %2 damage!" |
| `enemyDrain` | "%1 was drained of %2 %3!" |
| `enemyGain` | "%1 gained %2 %3!" |
| `enemyLoss` | "%1 lost %2 %3!" |
| `enemyNoDamage` | "%1 took no damage!" |
| `enemyNoHit` | "Miss! %1 took no damage!" |
| `enemyRecovery` | "%1 recovered %2 %3!" |
| `escapeFailure` | "However, it was unable to escape!" |
| `escapeStart` | "%1 has started to escape!" |
| `evasion` | "%1 evaded the attack!" |
| `expNext` | "To Next %1" |
| `expTotal` | "Current %1" |
| `file` | "File" |
| `levelUp` | "%1 is now %2 %3!" |
| `loadMessage` | "Load which file?" |
| `magicEvasion` | "%1 nullified the magic!" |
| `magicReflection` | "%1 reflected the magic!" |
| `meVolume` | "ME Volume" |
| `obtainExp` | "%1 %2 received!" |
| `obtainGold` | "%1\\G found!" |
| `obtainItem` | "%1 found!" |
| `obtainSkill` | "%1 learned!" |
| `partyName` | "%1's Party" |
| `possession` | "Possession" |
| `preemptive` | "%1 got the upper hand!" |
| `saveMessage` | "Save to which file?" |
| `seVolume` | "SE Volume" |
| `substitute` | "%1 protected %2!" |
| `surprise` | "%1 was surprised!" |
| `useItem` | "%1 uses %2!" |
| `victory` | "%1 was victorious!" |

---

## 10. Map ↔ System Relationship

### 10.1 Command Codes That Reference System.json

| Code | Name | References |
|---|---|---|
| 111 | Conditional Branch | Types: 0 (switch), 1 (variable), 4 (param), 7 (gold) |
| 121 | Control Switches | Switch ID range |
| 122 | Control Variables | Variable ID range |
| 125 | Change Gold | Currency |
| 317 | Change Items | Item ID |

### 10.2 Event Page Conditions

Event page conditions in map JSON reference:

- `switch1Id` / `switch2Id` → System.json switches
- `variableId` → System.json variables
- `itemId` → Items.json (not in System.json)
- `actorId` → Actors.json (not in System.json)

### 10.3 Conditional Branch Types

| Type | Check | Maps to |
|---|---|---|
| 0 | Switch | `switches[id]` |
| 1 | Variable | `variables[id]` |
| 2 | Self Switch | Event-local, no System.json |
| 3 | Timer | Engine state, no System.json |
| 4 | Actor Parameter | `terms.params[paramId]` |
| 5 | Enemy | Enemies.json (not in System.json) |
| 6 | Script | Direct script evaluation |
| 7 | Gold | `currencyUnit` display |
| 8 | Item | Items.json (not in System.json) |
| 9 | Weapon | Weapons.json (not in System.json) |
| 10 | Armor | Armors.json (not in System.json) |
| 11 | Button | Input state, no System.json |

---

## 11. Cross-Reference: Map001.json

Map001.json ("CHECKPOINT") references the following System.json data:

### 11.1 Switches Referenced

| Switch ID | Name | Used In |
|---|---|---|
| 1 | "Camp entry obtained" | Page 3 condition (trigger=0, empty) |
| 22 | "M: Pay up or alternate entry" | Control Switches (set ON after paying guards) |
| 173 | "Paid guards" | Control Switches (set ON after paying 50 silvers) |
| 278 | "Guards insulted" | Page 2 condition (guards refuse entry after insult) |
| 1000 | "DIRECTIONS OFF" | Page 2 condition (hides arrow events) |

### 11.2 Variables Referenced

No variables are directly referenced in Map001.json's event commands.

### 11.3 Items Referenced

| Item ID | Note |
|---|---|
| 1 | "Defiance" stat item (given in insult path) |
| 24 | Unknown (referenced in Guard Up event page 2 condition) |

---

## 12. Missing Data Files

The following RPG Maker MV data files are **NOT present** in the inputs directory but would be needed for complete transpilation:

| File | Contains | Needed For |
|---|---|---|
| `Actors.json` | Actor names, portraits, base parameters, skills | Character display names, actor conditionals |
| `Items.json` | Item names, descriptions, effects | Item names in "Change Items" (code 317) |
| `Weapons.json` | Weapon data | Weapon conditionals (code 111, type 9) |
| `Armors.json` | Armor data | Armor conditionals (code 111, type 10) |
| `Skills.json` | Skill definitions | Skill names in skill-related commands |
| `Classes.json` | Class/actor class data | Class-specific logic |
| `Enemies.json` | Enemy data | Enemy conditionals (code 111, type 5) |
| `Troops.json` | Enemy troop compositions | Battle event processing |
| `MapInfos.json` | Map names, parent hierarchy | Map label generation |
| `CommonEvents.json` | Shared/common event scripts | Processing cross-map events |

**Current inputs directory contains only:**
- `Map001.json`
- `Map002.json`
- `System.json`

---

## Appendix: Transpiler Implementation Notes

### Loading System.json

The transpiler should load `System.json` once at startup and make it available to all modules:

```python
def load_system_json(project_dir: str) -> dict:
    system_path = os.path.join(project_dir, "System.json")
    with open(system_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### Switch/Variable Name Resolution

```python
def get_switch_name(system: dict, switch_id: int) -> str:
    """Resolve switch ID to human-readable name."""
    switches = system.get('switches', [])
    if 0 <= switch_id < len(switches):
        return switches[switch_id]
    return f"unnamed_switch_{switch_id}"

def get_variable_name(system: dict, var_id: int) -> str:
    """Resolve variable ID to human-readable name."""
    variables = system.get('variables', [])
    if 0 <= var_id < len(variables):
        return variables[var_id]
    return f"unnamed_var_{var_id}"
```

### Parameter Index to Stat Name

```python
def get_param_name(system: dict, param_index: int) -> str:
    """Resolve parameter index to stat name via terms.params."""
    terms = system.get('terms', {})
    params = terms.get('params', [])
    if 0 <= param_index < len(params):
        return params[param_index]
    return f"param_{param_index}"
```

---

*Document Version: 1.0*  
*Generated for: RPG Maker MV to Ren'Py Transpiler*  
*Source Data: Claire's Quest 0.29.1 (System.json, Map001.json)*
