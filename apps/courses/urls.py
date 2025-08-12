from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, CursoViewSet, ModuloViewSet, LeccionViewSet

app_name = 'courses'

# Router para ViewSets
router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categorias')
router.register(r'cursos', CursoViewSet, basename='cursos')
router.register(r'modulos', ModuloViewSet, basename='modulos')
router.register(r'lecciones', LeccionViewSet, basename='lecciones')

urlpatterns = [
    # ViewSets
    path('', include(router.urls)),
]