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
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

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
    Serializer pour la réinitialisation de mot de passe
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value.strip())
            if not user.is_active:
                raise serializers.ValidationError(
                    'Ce compte utilisateur est désactivé.'
                )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Aucun utilisateur avec cette adresse email.'
            )
        return value


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