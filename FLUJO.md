# Flujo de trabajo: de tema a artículo publicado

Tres etapas: **generar → revisar → publicar**. Nada sale a la web sin que tú lo muevas.

## Requisitos

- LM Studio abierto con el servidor local encendido (pestaña Developer, puerto 1234).
- Terminal en `C:\AI\Proyectos\Web\euroaeuro`.

## Crear 4 artículos de golpe

```bat
cd C:\AI\Proyectos\Web\euroaeuro
.venv\Scripts\python.exe generar.py --lista
.venv\Scripts\python.exe generar.py --siguiente 4
```

- Tarda unos 35 segundos por artículo: **4 artículos ≈ 2,5 minutos**.
- Se guardan en `contenido\borradores\` como `slug.md` + `slug.json`.
- `temas.csv` marca esos temas como `generado`, así que la próxima vez empieza por el 5.

Al terminar verás algo así:

```
>> Cómo separar tus cuentas: la estructura de tres cuentas
   OK en 34s · 1592 palabras · como-separar-tus-cuentas-....md

Generados 4 de 4.
```

Si un artículo no pasa la validación, aparece `RECHAZADO (motivo)` y queda en
`contenido\borradores\_rechazados\` para que lo mires. No se pierde.

## Revisar

```bat
explorer contenido\borradores
```

Abre cada `.md` y léelo. Qué mirar, por orden de importancia:

1. **Que no invente datos.** Cifras oficiales, estadísticas o afirmaciones sobre la ley.
2. **Que no suene a máquina**: frases largas encadenadas, "es fundamental", "en el mundo actual".
3. **Que el consejo sea correcto.** Este es tu terreno y es lo que nadie más puede aportar.
4. **La meta descripción**: entre 140 y 160 caracteres, que resuma sin repetir la primera frase.

Corrige directamente en el archivo. Es Markdown: `##` para secciones, `**negrita**`, listas con `-`.

## Publicar

```bat
move contenido\borradores\mi-articulo.md contenido\publicado\
.venv\Scripts\python.exe construir_web.py
git add -A
git commit -m "Cuatro articulos nuevos"
git push
```

Para mover varios de golpe:

```bat
move contenido\borradores\*.md contenido\publicado\
```

GitHub Actions reconstruye y despliega solo. En 1-2 minutos están en `https://euroaeuro.eu`.

## Deshacer

Si publicas algo y te arrepientes:

```bat
move contenido\publicado\mi-articulo.md contenido\borradores\
.venv\Scripts\python.exe construir_web.py
git add -A && git commit -m "Retiro un articulo" && git push
```

## Detalles que conviene saber

- **El nombre del archivo es la URL.** `como-separar-tus-cuentas.md` → `/guias/como-separar-tus-cuentas/`.
  No lo cambies después de publicar: romperías los enlaces y lo que ya tenga Google.
- **La fecha es la del archivo.** Si quieres republicar algo "como nuevo", no cambies la fecha: se nota.
- **El `.json` lleva la categoría** (`ordena`, `ahorra`, `invierte`) para colocarlo en el pilar correcto.
  Si lo borras, el script lo clasifica por el título.
- **Genera en tandas de 3-4, no de 20.** Revisar 20 artículos de golpe no lo vas a hacer bien, y el
  contenido sin revisar es justo lo que te penaliza.

## Modelos

| Modelo | Velocidad | Cuándo usarlo |
|---|---|---|
| `qwen/qwen3.8-27b` (por defecto) | ~5,5 min | La calidad que quieres publicar |
| `qwen/qwen3.5-9b` | ~1 min | Borradores rápidos, para tantear un tema |

```bat
.venv\Scripts\python.exe generar.py --siguiente 1 --modelo qwen/qwen3.5-9b
```

Nota: los dos modelos tienen el razonamiento desactivado en su `model.yaml` de LM Studio.
Si una actualización lo reactiva, el modelo "piensa" hasta agotar los tokens y devuelve texto
vacío. Se arregla poniendo `defaultValue: false` en el campo `enableThinking`.
