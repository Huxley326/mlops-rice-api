# Guía del proyecto final: API para clasificar arroz

[No Verificado] El modelo y los archivos de entrenamiento se revisaron localmente. El estado actual de Databricks, Azure y GitHub debe confirmarse en las cuentas del proyecto.

Esta guía adapta el proceso del PDF del Módulo 3 al modelo de Kaggle Rice Cammeo/Osmancik. Los nombres nuevos elegidos para esta guía son `MLOPS_RICE_EAN` (Serving), `mlops-rice-api` (repositorio) y `api-arroz-mlops` (Container App). Si algún nombre ya está ocupado, cambia ese nombre en todos los pasos donde aparece.

## Antes de iniciar

El NB01 creó `Axis_Ratio = Major_Axis_Length / Minor_Axis_Length`, `Solidity = Area / Convex_Area` y `Circularity = 4*pi*Area / Perimeter^2`. El NB02 registró el modelo como `workspace.default.mlops_rice_model`; `Class` no es una entrada. El NB03 asignó `@champion` al modelo seleccionado. La API de esta carpeta envía diez variables, exactamente las de la firma del modelo ganador con ingeniería de variables.

El endpoint de estudiantes `MLOPS_UNIVEAN` apunta al modelo de estudiantes. Un nuevo endpoint de arroz evita cambiar el contrato de esa API. El Resource Group `rg-mlops-ean`, el Environment `env-mi-proyecto` y el ACR `acrricejavie20261017` pueden reutilizarse si siguen disponibles.

## Fase 1. Verificar y servir el modelo de arroz

1. Abre Databricks y ejecuta una celda Python para consultar el alias actual y la firma:

```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_registry_uri("databricks-uc")
nombre_modelo = "workspace.default.mlops_rice_model"
version = MlflowClient().get_model_version_by_alias(nombre_modelo, "champion")
print("Versión champion:", version.version)
info = mlflow.models.get_model_info(f"models:/{nombre_modelo}@champion")
print("Firma:", info.signature)
```

2. Comprueba que la firma tenga `Area`, `Perimeter`, `Major_Axis_Length`, `Minor_Axis_Length`, `Eccentricity`, `Convex_Area`, `Extent`, `Axis_Ratio`, `Solidity` y `Circularity`. Si aparece un conjunto diferente, detente y adapta `main.py` a la firma real.
3. En el menú de Databricks entra a **Serving** y pulsa **Create serving endpoint**. Escribe `MLOPS_RICE_EAN` como nombre. En **Served entities**, selecciona **My models - Unity Catalog**, el modelo `workspace.default.mlops_rice_model` y el número de versión que mostró la celda. Configura CPU Small y Scale to zero si la interfaz lo permite. Mantén desactivada Route optimization si usarás el token personal y el formato de URL de esta guía. Pulsa **Create**.
4. Espera a que el estado del endpoint sea **Ready**. Abre el endpoint, copia su URL de **Invocations** y comprueba que termine en `/serving-endpoints/MLOPS_RICE_EAN/invocations`.
5. En **Query endpoint**, pega el contenido de `ejemplo_databricks.json` y envía la consulta. También puedes probarlo en Anaconda Prompt con estos comandos, después de copiar el JSON a tu carpeta local:

```bat
set "DATABRICKS_URL=https://dbc-7f0ef5b6-ab12.cloud.databricks.com/serving-endpoints/MLOPS_RICE_EAN/invocations"
set "DATABRICKS_TOKEN=PEGA_AQUI_UN_TOKEN_NUEVO"
curl.exe -X POST "%DATABRICKS_URL%" -H "Authorization: Bearer %DATABRICKS_TOKEN%" -H "Content-Type: application/json" --data-binary @ejemplo_databricks.json
```

Resultado esperado: código HTTP 200 y un JSON con `predictions`. No abras la URL `/invocations` directamente en el navegador, porque una petición GET sin token no prueba el modelo. Los valores usados proceden de la primera fila del CSV de arroz; las tres variables creadas se calcularon con las fórmulas del NB01.

**Importante:** el endpoint de Serving queda configurado con un número de versión. Si NB03 promueve más adelante otra versión a `@champion`, edita el endpoint para que sirva la nueva versión. Cambiar el alias por sí solo no cambia la versión que Serving tiene configurada.

## Fase 2. Adaptar y probar la API

1. Crea una carpeta nueva `C:\Users\javie\mlops-rice-api` y copia dentro `main.py`, `requirements.txt`, `Dockerfile`, `.gitignore`, `ejemplo_api.json`, `ejemplo_databricks.json` y la carpeta `.github` de este paquete. La ruta final del workflow debe ser `C:\Users\javie\mlops-rice-api\.github\workflows\deploy.yml`.
2. `main.py` define diez campos requeridos y prohíbe campos adicionales. Envía los valores a Databricks en formato `dataframe_split`, en el orden de la firma. Interpreta `1` como Cammeo y `0` como Osmancik porque así construyó `label` el NB01. `/health` verifica que la API arrancó y que tiene configuradas las dos variables de conexión.
3. En Anaconda Prompt, prueba la API localmente:

```bat
cd /d C:\Users\javie\mlops-rice-api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set "DATABRICKS_URL=https://dbc-7f0ef5b6-ab12.cloud.databricks.com/serving-endpoints/MLOPS_RICE_EAN/invocations"
set "DATABRICKS_TOKEN=PEGA_AQUI_UN_TOKEN_NUEVO"
uvicorn main:app --reload
```

4. Deja esa ventana abierta. En otra ventana de Anaconda Prompt, dentro de la misma carpeta:

```bat
curl.exe http://127.0.0.1:8000/health
curl.exe -X POST http://127.0.0.1:8000/predecir -H "Content-Type: application/json" --data-binary @ejemplo_api.json
```

`/health` debe mostrar `databricks_configurado: true`; `/predecir` debe responder con `prediccion` y `clase`. El token se guarda solo en la ventana de terminal; no lo escribas en `main.py`, en el repositorio ni en el informe. Si el token compartido antes sigue activo, revócalo y genera uno nuevo.

## Fase 3. Reutilizar infraestructura de Azure

1. En Anaconda Prompt ejecuta `az login` y selecciona la suscripción **Azure for Students**.
2. Comprueba los recursos ya creados:

```bat
az account show --query "{name:name,id:id}" -o table
az group show --name rg-mlops-ean --query "{name:name,location:location}" -o table
az resource show --resource-group rg-mlops-ean --name env-mi-proyecto --resource-type Microsoft.App/managedEnvironments --query "{name:name,location:location,provisioningState:properties.provisioningState}" -o json
az acr show --resource-group rg-mlops-ean --name acrricejavie20261017 --query "{name:name,loginServer:loginServer,adminUserEnabled:adminUserEnabled,provisioningState:provisioningState}" -o json
```

3. Debes ver el grupo, el Environment y el ACR en la suscripción correcta. El Environment conocido estaba en Central US. Esta guía no vuelve a crear esos recursos; el workflow crea `api-arroz-mlops` en el mismo Environment.
4. Si todavía no tienes guardados los datos de acceso del ACR, recupéralos con `az acr credential show --resource-group rg-mlops-ean --name acrricejavie20261017`. Guarda `username` y el valor de `passwords[0].value` en un lugar privado. Si `adminUserEnabled` es false, las credenciales de administrador no estarán disponibles hasta habilitar esa opción en Azure.
5. `AZURE_CREDENTIALS` es el JSON de la identidad de servicio que usó GitHub Actions en el proyecto anterior. Un secreto guardado en GitHub no permite ver de nuevo su valor. Si no conservaste el JSON y `az ad sp create-for-rbac` todavía devuelve `Insufficient privileges`, necesitas que el administrador de Azure cree o repare una identidad con permiso Contributor sobre `rg-mlops-ean` y te entregue un método de autenticación válido. Cambiar de región no resuelve ese error de permisos.

## Fase 4. GitHub Actions y despliegue

1. En GitHub, crea bajo `Huxley326` un repositorio nuevo y vacío llamado `mlops-rice-api`. No marques opciones para crear README, `.gitignore` ni licencia desde GitHub; los archivos ya están en tu carpeta local.
2. En el repositorio nuevo entra a **Settings > Secrets and variables > Actions > New repository secret**. Crea exactamente estos cinco secretos:

| Secreto | Valor |
|---|---|
| `ACR_USERNAME` | `username` del ACR `acrricejavie20261017` |
| `ACR_PASSWORD` | Primera contraseña del mismo ACR |
| `AZURE_CREDENTIALS` | JSON completo de la identidad de servicio con acceso al Resource Group |
| `DATABRICKS_URL` | URL de invocación del endpoint de arroz, terminada en `/invocations` |
| `DATABRICKS_TOKEN` | Token vigente que pueda consultar el endpoint de arroz |

Los secretos de un repositorio de GitHub no aparecen automáticamente en otro. La URL del endpoint de estudiantes no sirve para esta API.

3. Revisa `.github/workflows/deploy.yml`. Usa el ACR existente, construye la imagen `rice-api` y crea o actualiza `api-arroz-mlops` mediante `az rest`, como en el PDF. No requiere volver a instalar la extensión `containerapp` en tu computadora. La contraseña de ACR y el token de Databricks se transmiten como secretos de Container Apps.
4. En Anaconda Prompt, dentro de la carpeta del nuevo proyecto, ejecuta:

```bat
cd /d C:\Users\javie\mlops-rice-api
git init
git add .
git commit -m "API de clasificacion de arroz"
git branch -M main
git remote add origin https://github.com/Huxley326/mlops-rice-api.git
git push -u origin main
```

Si ya existe `origin`, ejecuta `git remote set-url origin https://github.com/Huxley326/mlops-rice-api.git` en lugar de `git remote add origin ...`.
5. En GitHub, abre la pestaña **Actions** y el run **Desplegar API de arroz en Azure**. Espera a que todos los pasos terminen en verde. El último paso imprime `API pública: https://...` y consulta `/health`. Guarda esa URL.
6. Prueba `https://TU_NUEVA_API/health` y `https://TU_NUEVA_API/docs` en el navegador. En `/docs`, abre **POST /predecir**, pulsa **Try it out**, pega el contenido de `ejemplo_api.json` y pulsa **Execute**. Debes obtener HTTP 200 y una clase de arroz.
7. Desde Anaconda Prompt, sustituye la URL real de tu nueva API y ejecuta:

```bat
curl.exe -X POST "https://TU_NUEVA_API/predecir" -H "Content-Type: application/json" -d "{\"Area\":15231,\"Perimeter\":525.5789794921875,\"Major_Axis_Length\":229.7498779296875,\"Minor_Axis_Length\":85.09378814697266,\"Eccentricity\":0.9288820028305054,\"Convex_Area\":15617,\"Extent\":0.5728955268859863,\"Axis_Ratio\":2.699960630884914,\"Solidity\":0.9752833450726772,\"Circularity\":0.6928868314940618}"
```

Esa orden puede copiarse al informe después de reemplazar `https://TU_NUEVA_API` por la URL pública real. No necesita token, porque el token está en la configuración privada de la Container App.

## Entrega en un PDF de hasta cinco páginas

Complementa tu informe del Módulo 2 con una sección de despliegue. Incluye tu nombre completo, el nombre del dataset y un diccionario corto (siete medidas originales, tres medidas calculadas y la clase `Class`), el enlace real al repositorio nuevo, la URL pública real de `api-arroz-mlops`, el curl final con la URL real y los valores de arroz, y un texto de máximo 1000 palabras sobre NB01 a NB04 y Fases 1 a 4. Para que el profesor pueda comprobarlo, agrega evidencias breves de Serving en estado Ready, Actions en verde y la respuesta HTTP 200 de `/predecir`. Exporta a PDF y confirma que no supera cinco páginas.

No entregues el PDF mientras la URL pública siga siendo un marcador `TU_NUEVA_API` o el curl no responda. El repositorio y la URL pública no pueden inventarse antes de completar el despliegue.
