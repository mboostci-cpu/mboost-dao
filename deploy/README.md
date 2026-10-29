# Déploiement Hostinger

Cloner dans `/opt/mboost-cv-dao`, puis exécuter `bash deploy/install.sh` en root. Le script crée deux services indépendants, un utilisateur système sans shell et un répertoire de données privé. Il conserve le fichier de configuration existant et n'ouvre aucun port public.

Configurer le modèle et sa clé dans `/etc/mboost-cv-dao.env` côté VPS, puis redémarrer les deux services. Ne jamais publier ce fichier dans GitHub.

Accès privé depuis le PC : `ssh -L 8012:127.0.0.1:8012 UTILISATEUR@VOTRE_VPS`, puis ouvrir `http://localhost:8012`. Les traitements continuent ordinateur éteint dès que les deux services VPS sont actifs.

Une publication HTTPS nécessite un nom d'hôte, un reverse proxy et PUBLIC_MODE=1 avec APP_USER et APP_PASSWORD_SHA256. Ne pas exposer le port 8012 directement. Le mot de passe doit être choisi par l'utilisateur ; son hash est SHA-256. Compte unique, pas de portail multiclient.

Contrôle : `systemctl is-active mboost-cv-web mboost-cv-worker` et `curl --fail http://127.0.0.1:8012/health`.

Les traitements interrompus sont marqués interrupted ; leur relance est explicite pour éviter de répéter un appel facturé. Un fournisseur absent laisse les travaux blocked. Le ZIP contient le rapport et le brouillon PER-2 ; il n'autorise pas le dépôt ni la signature.
