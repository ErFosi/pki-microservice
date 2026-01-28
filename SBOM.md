# Análisis de SBOM y Vulnerabilidades

## Generación del SBOM

Para generar un Software Bill of Materials (SBOM) de las dependencias Python, utilicé la herramienta CycloneDX. Esta herramienta escanea el archivo `requirements.txt` y produce un SBOM en formato JSON compatible con estándares como CycloneDX.

### Comando utilizado:
```bash
cyclonedx-py requirements requirements.txt -o sbom.json
```

Este comando se ejecutó para ambos servicios (`ca-service` y `auth-gateway`), generando `sbom-ca-service.json` y `sbom-auth-gateway.json` respectivamente.

## Análisis de Vulnerabilidades con Grype

Para verificar vulnerabilidades en los SBOMs, utilicé Grype, una herramienta de Anchore que escanea directamente los archivos SBOM.

### Comando utilizado:
```bash
grype sbom:./sbom.json
```

### Resultados Iniciales (con vulnerabilidades intencionales)

Inicialmente, dejé intencionalmente algunas librerías con versiones vulnerables para demostrar el proceso. Los resultados del escaneo mostraron vulnerabilidades:

#### ca-service (antes de actualizar):
```
 ✔ Vulnerability DB                [updated]  
 ✔ Scanned for vulnerabilities     [4 vulnerability matches]  
   ├── by severity: 0 critical, 1 high, 2 medium, 1 low, 0 negligible
NAME          INSTALLED  FIXED IN  TYPE    VULNERABILITY        SEVERITY  EPSS         RISK   
cryptography  42.0.0     44.0.1    python  GHSA-79v4-65xg-pq4g  Low       1.7% (81st)  0.5    
cryptography  42.0.0     42.0.4    python  GHSA-6vqw-3v5j-54x4  High      0.3% (56th)  0.3    
cryptography  42.0.0     42.0.2    python  GHSA-9v9h-cgj8-h64p  Medium    0.2% (40th)  < 0.1  
cryptography  42.0.0     43.0.1    python  GHSA-h4gh-qq45-vh27  Medium    N/A          N/A
```

#### auth-gateway (antes de actualizar):
```
 ✔ Scanned for vulnerabilities     [5 vulnerability matches]  
   ├── by severity: 1 critical, 3 high, 1 medium, 0 low, 0 negligible
NAME              INSTALLED  FIXED IN  TYPE    VULNERABILITY        SEVERITY  EPSS          RISK   
python-multipart  0.0.6      0.0.7     python  GHSA-2jv5-9r88-3w3p  High      2.5% (84th)   1.9    
python-jose       3.3.0      3.4.0     python  GHSA-6c5p-j8vq-pqhj  Critical  0.7% (71st)   0.6    
python-jose       3.3.0      3.4.0     python  GHSA-cjwg-qfpm-7377  Medium    0.2% (41st)   0.1    
python-multipart  0.0.6      0.0.18    python  GHSA-59g5-xgcq-4qw3  High      0.1% (30th)   < 0.1  
python-multipart  0.0.6      0.0.22    python  GHSA-wp53-j4wj-2cfg  High      < 0.1% (3rd)  < 0.1
```

### Resultados Después de Actualizar

Después de actualizar las dependencias a las versiones más recientes disponibles:
- `cryptography==46.0.4`
- `python-jose==3.5.0`
- `python-multipart==0.0.22`

Y regenerar los SBOMs, el análisis con Grype no reportó ningún error:

#### ca-service (después de actualizar):
```
 ✔ Scanned for vulnerabilities     [0 vulnerability matches]  
   ├── by severity: 0 critical, 0 high, 0 medium, 0 low, 0 negligible
No vulnerabilities found
```

#### auth-gateway (después de actualizar):
```
 ✔ Scanned for vulnerabilities     [0 vulnerability matches]  
   ├── by severity: 0 critical, 0 high, 0 medium, 0 low, 0 negligible
No vulnerabilities found
```

Esto asegura que el código esté libre de vulnerabilidades conocidas en las dependencias más recientes.</content>
<parameter name="filePath">/home/alvaro/pki-microservice/SBOM.md
