from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Stagiaire


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour l'authentification avec login/password
    """
    login = serializers.CharField(max_length=120)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')

        if login and password:
            # Nettoyer les espaces et convertir en minuscules
            login = login.strip().lower()
            password = password.strip()

            # Authentifier l'utilisateur
            user = authenticate(
                request=self.context.get('request'),
                username=login,
                password=password
            )

            if not user:
                msg = 'Impossible de se connecter avec ces identifiants.'
                raise serializers.ValidationError(msg, code='authorization')

            if not user.is_active:
                msg = 'Ce compte utilisateur est désactivé.'
                raise serializers.ValidationError(msg, code='authorization')

            attrs['user'] = user
            return attrs
        else:
            msg = 'Le login et le mot de passe sont requis.'
            raise serializers.ValidationError(msg, code='authorization')


class LogoutSerializer(serializers.Serializer):
    """
    Serializer pour la déconnexion
    """
    refresh_token = serializers.CharField(required=True, help_text='Token de rafraîchissement JWT à blacklister')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher le profil utilisateur selon le rôle
    """
    stagiaire_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'nom', 'prenom', 'login', 'email', 'role',
            'date_joined', 'stagiaire_profile'
        ]

    def get_stagiaire_profile(self, obj):
        """
        Retourne les informations du profil stagiaire si applicable
        """
        if obj.role == 'STAGIAIRE' and hasattr(obj, 'stagiaire_profile'):
            return {
                'societe': obj.stagiaire_profile.societe
            }
        return None


class StagiaireProfileSerializer(serializers.ModelSerializer):
    """
    Serializer spécifique pour le profil stagiaire
    """
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Stagiaire
        fields = ['user', 'societe']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe
    """
    old_password = serializers.CharField(
        write_only=True,
        help_text="Mot de passe actuel de l'utilisateur",
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        help_text="Nouveau mot de passe (minimum 8 caractères, doit contenir lettres et chiffres)",
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirmation du nouveau mot de passe (doit être identique)",
        style={'input_type': 'password'},
        min_length=8
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value.strip()):
            raise serializers.ValidationError('Ancien mot de passe incorrect.')
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password', '').strip()
        confirm_password = attrs.get('confirm_password', '').strip()

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas.'
            })

        # Valider le nouveau mot de passe selon les règles Django
        try:
            validate_password(new_password, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': e.messages
            })

        return attrs

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password'].strip()
        user.set_password(new_password)
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer pour la demande de réinitialisation de mot de passe
    """
    email = serializers.EmailField(
        help_text="Adresse email de l'utilisateur pour recevoir le lien de réinitialisation",
        required=True
    )

    def validate_email(self, value):
        """
        Valide l'email mais ne révèle pas si l'utilisateur existe pour des raisons de sécurité
        """
        email = value.strip().lower()

        # Validation de format de base (déjà fait par EmailField)
        if not email:
            raise serializers.ValidationError('L\'adresse email ne peut pas être vide.')

        # Note: En production, nous ne devrions pas révéler si l'utilisateur existe
        # mais pour le développement, gardons cette validation pour debugging
        try:
            user = User.objects.get(email__iexact=email)
            if not user.is_active:
                # Pour la sécurité, on ne révèle pas que le compte existe mais est inactif
                # en production, on devrait traiter cela silencieusement
                pass
        except User.DoesNotExist:
            # Pour la sécurité, on ne révèle pas que l'utilisateur n'existe pas
            # en production, on devrait traiter cela silencieusement
            pass

        return email


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour confirmer la réinitialisation de mot de passe avec token
    """
    uidb64 = serializers.CharField(
        help_text="UID encodé en base64 de l'utilisateur",
        required=True
    )
    token = serializers.CharField(
        help_text="Token de réinitialisation généré par Django",
        required=True
    )
    new_password = serializers.CharField(
        write_only=True,
        help_text="Nouveau mot de passe (minimum 8 caractères)",
        style={'input_type': 'password'},
        min_length=8,
        required=True
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirmation du nouveau mot de passe",
        style={'input_type': 'password'},
        min_length=8,
        required=True
    )

    def validate(self, attrs):
        new_password = attrs.get('new_password', '').strip()
        confirm_password = attrs.get('confirm_password', '').strip()

        # Vérifier que les mots de passe correspondent
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas.'
            })

        # Valider le nouveau mot de passe selon les règles Django
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': e.messages
            })

        # Valider le token et l'UID
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        from django.contrib.auth.tokens import default_token_generator

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Lien de réinitialisation invalide.')

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError('Token de réinitialisation expiré ou invalide.')

        if not user.is_active:
            raise serializers.ValidationError('Ce compte utilisateur est désactivé.')

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password'].strip()
        user.set_password(new_password)
        user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'utilisateurs (admin uniquement)
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    societe = serializers.CharField(required=False, allow_blank=True, max_length=180)

    class Meta:
        model = User
        fields = [
            'nom', 'prenom', 'login', 'email', 'role',
            'password', 'confirm_password', 'societe'
        ]

    def validate_login(self, value):
        # Nettoyer et convertir en minuscules
        login = value.strip().lower()
        if User.objects.filter(login__iexact=login).exists():
            raise serializers.ValidationError('Ce login existe déjà.')
        return login

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Cette adresse email existe déjà.')
        return email

    def validate(self, attrs):
        password = attrs.get('password', '').strip()
        confirm_password = attrs.get('confirm_password', '').strip()

        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas.'
            })

        # Valider le mot de passe selon les règles Django
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': e.messages
            })

        return attrs

    def create(self, validated_data):
        # Retirer les champs qui ne sont pas dans le modèle User
        societe = validated_data.pop('societe', None)
        confirm_password = validated_data.pop('confirm_password')
        password = validated_data.pop('password').strip()

        # Nettoyer les données
        validated_data['login'] = validated_data['login'].strip().lower()
        validated_data['email'] = validated_data['email'].strip().lower()
        validated_data['nom'] = validated_data['nom'].strip()
        validated_data['prenom'] = validated_data['prenom'].strip()

        # Créer l'utilisateur
        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Créer le profil stagiaire si nécessaire
        if user.role == 'STAGIAIRE':
            Stagiaire.objects.create(
                user=user,
                societe=societe.strip() if societe else None
            )

        return user


class StagiaireCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de stagiaires avec validation stricte
    """
    # Champs utilisateur
    nom = serializers.CharField(max_length=120, required=True)
    prenom = serializers.CharField(max_length=120, required=True)
    login = serializers.CharField(max_length=120, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    # Champ stagiaire
    societe = serializers.CharField(max_length=180, required=True)

    class Meta:
        model = Stagiaire
        fields = [
            'nom', 'prenom', 'login', 'email', 'password',
            'confirm_password', 'societe'
        ]

    def validate_nom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le nom ne peut pas être vide.')
        return value.strip()

    def validate_prenom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le prénom ne peut pas être vide.')
        return value.strip()

    def validate_login(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le login ne peut pas être vide.')

        login = value.strip().lower()

        # Vérifier l'unicité du login
        if User.objects.filter(login__iexact=login).exists():
            raise serializers.ValidationError('Ce login existe déjà.')

        return login

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('L\'email ne peut pas être vide.')

        email = value.strip().lower()

        # Vérifier l'unicité de l'email
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Cette adresse email existe déjà.')

        return email

    def validate_societe(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('La société ne peut pas être vide.')
        return value.strip()

    def validate(self, attrs):
        password = attrs.get('password', '').strip()
        confirm_password = attrs.get('confirm_password', '').strip()

        # Vérification des mots de passe
        if not password:
            raise serializers.ValidationError({
                'password': 'Le mot de passe ne peut pas être vide.'
            })

        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas.'
            })

        # Validation de la force du mot de passe
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': e.messages
            })

        # Vérifier l'unicité de la paire nom/login (après normalisation)
        nom = attrs.get('nom', '').strip()
        login = attrs.get('login', '').strip().lower()

        if User.objects.filter(
            nom__iexact=nom,
            login__iexact=login
        ).exists():
            raise serializers.ValidationError(
                'La combinaison nom/login existe déjà.'
            )

        return attrs

    def create(self, validated_data):
        # Retirer les champs non-User
        societe = validated_data.pop('societe')
        confirm_password = validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        # Créer l'utilisateur
        user_data = {
            'nom': validated_data['nom'],
            'prenom': validated_data['prenom'],
            'login': validated_data['login'],
            'email': validated_data['email'],
            'role': 'STAGIAIRE'
        }

        user = User.objects.create_user(
            password=password,
            **user_data
        )

        # Créer le profil stagiaire
        stagiaire = Stagiaire.objects.create(
            user=user,
            societe=societe
        )

        return stagiaire


class StagiaireUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour de stagiaires
    """
    # Champs utilisateur
    nom = serializers.CharField(max_length=120, required=False)
    prenom = serializers.CharField(max_length=120, required=False)
    login = serializers.CharField(max_length=120, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    is_active = serializers.BooleanField(required=False)

    # Champ stagiaire
    societe = serializers.CharField(max_length=180, required=False)

    class Meta:
        model = Stagiaire
        fields = [
            'nom', 'prenom', 'login', 'email', 'password',
            'confirm_password', 'societe', 'is_active'
        ]

    def validate_nom(self, value):
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError('Le nom ne peut pas être vide.')
        return value.strip() if value else value

    def validate_prenom(self, value):
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError('Le prénom ne peut pas être vide.')
        return value.strip() if value else value

    def validate_login(self, value):
        if value is not None:
            if not value or not value.strip():
                raise serializers.ValidationError('Le login ne peut pas être vide.')

            login = value.strip().lower()

            # Vérifier l'unicité du login (exclure l'utilisateur actuel)
            if User.objects.filter(login__iexact=login).exclude(
                id=self.instance.user.id
            ).exists():
                raise serializers.ValidationError('Ce login existe déjà.')

            return login
        return value

    def validate_email(self, value):
        if value is not None:
            if not value or not value.strip():
                raise serializers.ValidationError('L\'email ne peut pas être vide.')

            email = value.strip().lower()

            # Vérifier l'unicité de l'email (exclure l'utilisateur actuel)
            if User.objects.filter(email__iexact=email).exclude(
                id=self.instance.user.id
            ).exists():
                raise serializers.ValidationError('Cette adresse email existe déjà.')

            return email
        return value

    def validate_societe(self, value):
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError('La société ne peut pas être vide.')
        return value.strip() if value else value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        # Vérification des mots de passe si fournis
        if password is not None or confirm_password is not None:
            if password != confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': 'Les mots de passe ne correspondent pas.'
                })

            if password and not password.strip():
                raise serializers.ValidationError({
                    'password': 'Le mot de passe ne peut pas être vide.'
                })

            # Validation de la force du mot de passe
            if password:
                try:
                    validate_password(password.strip(), self.instance.user)
                except ValidationError as e:
                    raise serializers.ValidationError({
                        'password': e.messages
                    })

        # Vérifier l'unicité de la paire nom/login si modifiés
        nom = attrs.get('nom')
        login = attrs.get('login')

        if nom is not None or login is not None:
            final_nom = nom if nom is not None else self.instance.user.nom
            final_login = login if login is not None else self.instance.user.login

            if User.objects.filter(
                nom__iexact=final_nom,
                login__iexact=final_login
            ).exclude(id=self.instance.user.id).exists():
                raise serializers.ValidationError(
                    'La combinaison nom/login existe déjà.'
                )

        return attrs

    def update(self, instance, validated_data):
        # Séparer les champs utilisateur et stagiaire
        user_fields = ['nom', 'prenom', 'login', 'email', 'password', 'is_active']
        stagiaire_fields = ['societe']

        user_data = {}
        stagiaire_data = {}

        for field, value in validated_data.items():
            if field in user_fields:
                if field not in ['password', 'confirm_password']:
                    user_data[field] = value
            elif field in stagiaire_fields:
                stagiaire_data[field] = value

        # Retirer confirm_password
        validated_data.pop('confirm_password', None)

        # Mettre à jour l'utilisateur
        user = instance.user
        for field, value in user_data.items():
            setattr(user, field, value)

        # Mettre à jour le mot de passe si fourni
        password = validated_data.get('password')
        if password:
            user.set_password(password.strip())

        user.save()

        # Mettre à jour le stagiaire
        for field, value in stagiaire_data.items():
            setattr(instance, field, value)

        instance.save()

        return instance


class StagiaireDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage détaillé d'un stagiaire
    """
    # Informations utilisateur
    id = serializers.IntegerField(source='user.id', read_only=True)
    nom = serializers.CharField(source='user.nom', read_only=True)
    prenom = serializers.CharField(source='user.prenom', read_only=True)
    login = serializers.CharField(source='user.login', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)

    # Statistiques des parcours
    nombre_parcours = serializers.SerializerMethodField()
    parcours_termines = serializers.SerializerMethodField()
    note_moyenne = serializers.SerializerMethodField()

    class Meta:
        model = Stagiaire
        fields = [
            'id', 'nom', 'prenom', 'login', 'email', 'societe',
            'is_active', 'date_joined', 'last_login',
            'nombre_parcours', 'parcours_termines', 'note_moyenne'
        ]

    def get_nombre_parcours(self, obj):
        return obj.parcours.count()

    def get_parcours_termines(self, obj):
        return obj.parcours.filter(statut='TERMINE').count()

    def get_note_moyenne(self, obj):
        from django.db.models import Avg
        avg_note = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(avg=Avg('note_obtenue'))['avg']

        return round(avg_note, 2) if avg_note else None