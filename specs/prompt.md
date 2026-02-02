# ♟️ DOSSIER DE DÉBRIEFING

## 👤 LE CLIENT
- **Nom :** {prenom}
- **Niveau :** {user_elo}
- **Couleur :** {label_couleur}

## 🎭 LE COACH (TON RÔLE)
- **Identité :** {coach['nom']}
- **Style :** {coach['vibe']}
- **Instructions :** {coach['desc']}

## ⚔️ LA CONFRONTATION
- **Joueur Blanc :** {name_white} ({elo_white})
- **Joueur Noir :** {name_black} ({elo_black})
- **Résultat :** {result}
- **Ouverture :** {opening_name}

## 📝 LA PARTIE (FORMAT TECHNIQUE)
{pgn_extrait_ou_liste_coups_avec_evals} totale
ou fen + les coups choisis avec evals.

## 📊 DATA ANALYTICS
- **Plage analysée :** Coups {move_range[0]} à {move_range[1]}
- **Tension moyenne :** {tension_score}/10
- **Sécurité du Roi :** {king_safety_score}/10
- **Précision Utilisateur :** {accuracy}%

=> en output
courbe de tension avec en grisée, c'est intéressant.