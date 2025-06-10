# Flujo de Desarrollo Multi-Ambiente

## Ambientes y Propósito

| Ambiente | Distribución | Tag Pattern | API Endpoint | Propósito |
|----------|-------------|-------------|--------------|-----------|
| **Local** | Solo desarrollo local | - | `localhost:8000` o `dev.bugster.api` | Desarrollo individual |
| **Development** | Pre-releases públicos | `v*-beta.*`, `v*-rc.*`, `v*-alpha.*` | `dev.bugster.api` | Testing público antes de producción |
| **Production** | Releases finales | `v*.*.*` | `api.bugster.app` | Usuarios finales |

## Flujo de Trabajo

### 1. Desarrollo Local (Sin Releases)
```bash
# Desarrollo en rama feature - SOLO LOCAL
git checkout -b feature/nueva-funcionalidad

# Opción 1: Desarrollo contra API local
echo "BUGSTER_ENVIRONMENT=local" > .env
echo "BUGSTER_API_URL=http://localhost:8000" >> .env
bugster test  # → Conecta a localhost:8000

# Opción 2: Desarrollo contra API development remoto
BUGSTER_ENVIRONMENT=development bugster test  # → Conecta a dev.bugster.api

# NO se crean releases desde local
```

### 2. Pre-Release Development (Público)
```bash
# Cuando la feature está lista para testing público
git checkout main  # o rama de release
git merge feature/nueva-funcionalidad

# Release para testing público
git tag v1.2.3-beta.1
git push origin --tags

# El CI construye automáticamente con environment=development
# Cualquiera puede instalar: dev.bugster.api
curl -sSL .../releases/download/v1.2.3-beta.1/install.sh | bash
```

### 3. Production Release
```bash
# Cuando el beta está aprobado
git tag v1.2.3
git push origin --tags

# El CI construye automáticamente con environment=production
# Distribución final: api.bugster.app
curl -sSL .../releases/download/v1.2.3/install.sh | bash
```

## Configuración para Usuarios

### Variables de Ambiente
```bash
# Desarrollo local: Los desarrolladores eligen su API
export BUGSTER_ENVIRONMENT=local          # → localhost:8000
export BUGSTER_ENVIRONMENT=development    # → dev.bugster.api

# Pre-releases instalados: Automáticamente usan development
# → dev.bugster.api (sin configuración extra)

# Production instalado: Automáticamente usa production  
# → api.bugster.app (sin configuración extra)
```

### Archivo de configuración local
```yaml
# ~/.bugsterrc (para desarrollo local)
environment: local  # o development
api_url: http://localhost:8000  # o custom
log_level: DEBUG
```

## Ventajas de este Enfoque

1. **Simplicidad**: Solo 2 APIs (development y production)
2. **Flexibilidad Local**: Los desarrolladores pueden conectar a localhost o development
3. **Releases Simples**: Solo pre-releases (beta/rc) y production
4. **Sin Confusión**: Los usuarios instalan automáticamente la configuración correcta
5. **Testing Público**: Las betas están disponibles para testing comunitario

## Testing de la Configuración

```python
# tests/test_environment_config.py
def test_environment_detection():
    # Test local environment
    os.environ["BUGSTER_ENVIRONMENT"] = "local"
    settings = LibsSettings()
    assert settings.bugster_api_url == "http://localhost:8000"
    
    # Test development environment  
    os.environ["BUGSTER_ENVIRONMENT"] = "development"
    settings = LibsSettings()
    assert settings.bugster_api_url == "https://dev.bugster.api"
    
    # Test production environment
    os.environ["BUGSTER_ENVIRONMENT"] = "production" 
    settings = LibsSettings()
    assert settings.bugster_api_url == "https://api.bugster.app"
```