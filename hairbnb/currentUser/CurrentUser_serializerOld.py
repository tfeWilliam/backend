# from rest_framework import serializers
# from hairbnb.models import (
#     TblUser, TblCoiffeuse, TblClient, TblRue, TblLocalite, TblAdresse,
#     TblRole, TblSexe, TblType, TblSalon, TblCoiffeuseSalon
# )
#
#
# # 🔹 Serializer pour la Localité
# class LocaliteSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblLocalite
#         fields = ['idTblLocalite', 'commune', 'code_postal']
#
#
# class TblLocaliteSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblLocalite
#         fields = ['commune', 'code_postal']
#
#
# # 🔹 Serializer pour la Rue
# class RueSerializer(serializers.ModelSerializer):
#     localite = LocaliteSerializer()
#
#     class Meta:
#         model = TblRue
#         fields = ['idTblRue', 'nom_rue', 'localite']
#
#
# class TblRueSerializer(serializers.ModelSerializer):
#     localite = TblLocaliteSerializer(read_only=True)
#
#     class Meta:
#         model = TblRue
#         fields = ['nom_rue', 'localite']
#
#
# # 🔹 Serializer pour l'Adresse
# class AdresseSerializer(serializers.ModelSerializer):
#     rue = RueSerializer()
#
#     class Meta:
#         model = TblAdresse
#         fields = ['idTblAdresse', 'numero', 'rue']
#
#
# class TblAdresseSerializer(serializers.ModelSerializer):
#     rue = TblRueSerializer(read_only=True)
#
#     class Meta:
#         model = TblAdresse
#         fields = ['numero', 'rue']
#
#
# # 🔹 Serializer pour le Rôle
# class RoleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblRole
#         fields = ['idTblRole', 'nom']
#
#
# class TblRoleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblRole
#         fields = ['libelle']
#
#
# # 🔹 Serializer pour le Sexe
# class SexeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblSexe
#         fields = ['idTblSexe', 'libelle']
#
#
# class TblSexeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblSexe
#         fields = ['libelle']
#
#
# # 🔹 Serializer pour le Type
# class TypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblType
#         fields = ['idTblType', 'libelle']
#
#
# class TblTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblType
#         fields = ['libelle']
#
#
# # 🔹 Serializer pour l'Utilisateur (User)
# class UserSerializer(serializers.ModelSerializer):
#     adresse = AdresseSerializer()
#     role = RoleSerializer()
#     sexe_ref = SexeSerializer()
#     type_ref = TypeSerializer()
#
#     class Meta:
#         model = TblUser
#         fields = [
#             'idTblUser', 'uuid', 'nom', 'prenom', 'email', 'numero_telephone',
#             'date_naissance', 'is_active', 'photo_profil', 'adresse',
#             'role', 'sexe_ref', 'type_ref'
#         ]
#
#
# # 🔹 Serializer simple pour la Coiffeuse (sans user details)
# class CoiffeuseSimpleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblCoiffeuse
#         fields = ['idTblUser', 'nom_commercial']
#
#
# # 🔹 Serializer COMPLET pour la Coiffeuse
# class CoiffeuseSerializer(serializers.ModelSerializer):
#     user = UserSerializer(source='idTblUser')
#
#     class Meta:
#         model = TblCoiffeuse
#         fields = [
#             'idTblUser', 'nom_commercial', 'user'
#         ]
#
#
# class TblCoiffeuseSerializer(serializers.ModelSerializer):
#     salons = serializers.SerializerMethodField()
#     salon_principal = serializers.SerializerMethodField()
#     est_proprietaire = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblCoiffeuse
#         fields = ['nom_commercial', 'salons', 'salon_principal', 'est_proprietaire']
#
#     def get_salons(self, obj):
#         """Récupère tous les salons où la coiffeuse travaille avec gestion d'erreurs"""
#         try:
#             salon_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=obj)
#             salon_data = []
#
#             for relation in salon_relations:
#                 try:
#                     salon = relation.salon
#                     salon_info = {
#                         'idTblSalon': salon.idTblSalon,
#                         'nom_salon': getattr(salon, 'nom_salon', ''),
#                         'est_proprietaire': relation.est_proprietaire
#                     }
#                     salon_data.append(salon_info)
#                 except Exception as e:
#                     print(f"🔍 ❌ Erreur dans get_salons pour relation {relation.id}: {str(e)}")
#                     continue
#
#             return salon_data
#         except Exception as e:
#             print(f"🔍 ❌ Erreur dans get_salons: {str(e)}")
#             return []
#
#     def get_salon_principal(self, obj):
#         """Récupère le salon dont la coiffeuse est propriétaire avec gestion d'erreurs"""
#         try:
#             relation = TblCoiffeuseSalon.objects.filter(
#                 coiffeuse=obj,
#                 est_proprietaire=True
#             ).first()
#
#             if relation and relation.salon:
#                 salon = relation.salon
#                 salon_data = {
#                     'idTblSalon': salon.idTblSalon,
#                     'nom_salon': getattr(salon, 'nom_salon', ''),
#                     'slogan': getattr(salon, 'slogan', ''),
#                     'numero_tva': getattr(salon, 'numero_tva', ''),
#                 }
#
#                 # Gestion sécurisée du logo
#                 try:
#                     if salon.logo_salon:
#                         salon_data['logo_salon'] = salon.logo_salon.url
#                     else:
#                         salon_data['logo_salon'] = None
#                 except Exception as e:
#                     print(f"🔍 ❌ Erreur logo salon: {e}")
#                     salon_data['logo_salon'] = None
#
#                 return salon_data
#             return None
#         except Exception as e:
#             print(f"🔍 ❌ Erreur dans get_salon_principal: {str(e)}")
#             return None
#
#     def get_est_proprietaire(self, obj):
#         """Vérifie si la coiffeuse est propriétaire d'au moins un salon avec gestion d'erreurs"""
#         try:
#             return TblCoiffeuseSalon.objects.filter(
#                 coiffeuse=obj,
#                 est_proprietaire=True
#             ).exists()
#         except Exception as e:
#             print(f"🔍 ❌ Erreur dans get_est_proprietaire: {str(e)}")
#             return False
#
#
# # 🔹 Serializer COMPLET pour le Client
# class ClientSerializer(serializers.ModelSerializer):
#     user = UserSerializer(source='idTblUser')
#
#     class Meta:
#         model = TblClient
#         fields = ['idTblUser', 'user']
#
#
# # 🔹 Serializer simple pour le Salon
# class SalonSimpleSerializer(serializers.ModelSerializer):
#     adresse = AdresseSerializer(read_only=True)
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon', 'nom_salon', 'slogan', 'logo_salon',
#             'adresse', 'position', 'numero_tva'
#         ]
#
#
# # 🔹 Serializer COMPLET pour le Salon
# class SalonSerializer(serializers.ModelSerializer):
#     adresse = AdresseSerializer(read_only=True)
#     coiffeuses = CoiffeuseSimpleSerializer(many=True, read_only=True)
#     proprietaire = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon', 'nom_salon', 'slogan', 'a_propos',
#             'logo_salon', 'adresse', 'position', 'numero_tva',
#             'coiffeuses', 'proprietaire'
#         ]
#
#     def get_proprietaire(self, obj):
#         """Récupère la coiffeuse propriétaire du salon"""
#         proprietaire = obj.get_proprietaire()
#         if proprietaire:
#             return CoiffeuseSimpleSerializer(proprietaire).data
#         return None
#
#
# class TblSalonSerializer(serializers.ModelSerializer):
#     adresse = TblAdresseSerializer(read_only=True)
#     position = serializers.CharField(read_only=True)
#
#     class Meta:
#         model = TblSalon
#         fields = ['idTblSalon', 'nom_salon', 'slogan', 'a_propos', 'logo_salon', 'adresse', 'position', 'numero_tva']
#
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         # Convertir l'URL de l'image en URL complète avec gestion d'erreurs
#         try:
#             if representation['logo_salon']:
#                 request = self.context.get('request')
#                 if request is not None:
#                     representation['logo_salon'] = request.build_absolute_uri(representation['logo_salon'])
#         except Exception as e:
#             print(f"🔍 ❌ Erreur build_absolute_uri: {e}")
#             representation['logo_salon'] = None
#         return representation
#
#
# # 🔹 Serializer pour la relation Coiffeuse-Salon
# class CoiffeuseSalonSerializer(serializers.ModelSerializer):
#     coiffeuse = CoiffeuseSimpleSerializer(read_only=True)
#     salon = SalonSimpleSerializer(read_only=True)
#
#     class Meta:
#         model = TblCoiffeuseSalon
#         fields = ['idCoiffeuseSalon', 'coiffeuse', 'salon', 'est_proprietaire']
#
#
# class CurrentUserSerializer(serializers.ModelSerializer):
#     role = serializers.SerializerMethodField()
#     sexe = serializers.SerializerMethodField()
#     type = serializers.SerializerMethodField()
#     adresse = TblAdresseSerializer(read_only=True)
#     coiffeuse_data = serializers.SerializerMethodField(source='get_coiffeuse_data')
#
#     class Meta:
#         model = TblUser
#         fields = [
#             'idTblUser', 'uuid', 'nom', 'prenom', 'email',
#             'numero_telephone', 'date_naissance', 'is_active',
#             'photo_profil', 'adresse', 'role', 'sexe', 'type',
#             'coiffeuse_data'
#         ]
#
#     def get_role(self, obj):
#         try:
#             return obj.role.nom if obj.role else None
#         except Exception as e:
#             print(f"🔍 ❌ Erreur get_role: {e}")
#             return None
#
#     def get_sexe(self, obj):
#         try:
#             return obj.sexe_ref.libelle if obj.sexe_ref else None
#         except Exception as e:
#             print(f"🔍 ❌ Erreur get_sexe: {e}")
#             return None
#
#     def get_type(self, obj):
#         try:
#             return obj.type_ref.libelle if obj.type_ref else None
#         except Exception as e:
#             print(f"🔍 ❌ Erreur get_type: {e}")
#             return None
#
#     def get_coiffeuse_data(self, obj):
#         """
#         Récupère les données de coiffeuse avec gestion complète des erreurs
#         """
#         try:
#             print(f"🔍 DEBUG get_coiffeuse_data pour user {obj.idTblUser}")
#             print(f"🔍 hasattr(obj, 'coiffeuse'): {hasattr(obj, 'coiffeuse')}")
#
#             if hasattr(obj, 'coiffeuse'):
#                 coiffeuse_obj = obj.coiffeuse
#                 print(f"🔍 coiffeuse_obj: {coiffeuse_obj}")
#
#                 if coiffeuse_obj:
#                     print(f"🔍 Début sérialisation TblCoiffeuseSerializer...")
#                     serializer_data = TblCoiffeuseSerializer(coiffeuse_obj, context=self.context)
#                     print(f"🔍 Serializer créé, récupération data...")
#                     result = serializer_data.data
#                     print(f"🔍 Serialization réussie: {result}")
#                     return result
#                 else:
#                     print("🔍 ❌ coiffeuse_obj est None")
#                     return None
#             else:
#                 print("🔍 ❌ hasattr(obj, 'coiffeuse') est False")
#                 return None
#
#         except Exception as e:
#             print(f"🔍 ❌ ERREUR dans get_coiffeuse_data: {str(e)}")
#             import traceback
#             print(f"🔍 ❌ Traceback: {traceback.format_exc()}")
#             # Ne pas faire planter, retourner None
#             return None
#
#     def to_representation(self, instance):
#         try:
#             representation = super().to_representation(instance)
#             # Convertir l'URL de la photo de profil en URL complète avec gestion d'erreurs
#             try:
#                 if representation.get('photo_profil'):
#                     request = self.context.get('request')
#                     if request is not None:
#                         representation['photo_profil'] = request.build_absolute_uri(representation['photo_profil'])
#             except Exception as e:
#                 print(f"🔍 ❌ Erreur photo_profil URL: {e}")
#                 representation['photo_profil'] = None
#
#             # Renommer coiffeuse_data en coiffeuse pour maintenir la cohérence
#             if 'coiffeuse_data' in representation:
#                 representation['coiffeuse'] = representation.pop('coiffeuse_data')
#
#             return representation
#         except Exception as e:
#             print(f"🔍 ❌ Erreur dans to_representation: {e}")
#             import traceback
#             print(f"🔍 ❌ Traceback: {traceback.format_exc()}")
#             # Retourner une représentation minimale pour éviter le crash
#             return {
#                 'idTblUser': getattr(instance, 'idTblUser', None),
#                 'nom': getattr(instance, 'nom', ''),
#                 'prenom': getattr(instance, 'prenom', ''),
#                 'error': 'Erreur de sérialisation'
#             }
