# 📌 Aclaración: Nombre del Ejecutable

## Importante

**El nombre del ejecutable es `installer`, no `CLI-agent-installer`.**

---

## Diferencia entre Paquete y Ejecutable

| Aspecto | Nombre | Uso |
|---|---|---|
| **Nombre del paquete** | `CLI-agent-installer` | Instalación: `pip install CLI-agent-installer` |
| **Nombre del ejecutable** | `installer` | Uso: `installer <comando>` |

---

## Ejemplos Correctos

### Instalación

```bash
pip install CLI-agent-installer
```

### Uso

```bash
# Inicializar en un proyecto
installer init . --repo "usuario/proyecto"

# Ejecutar checklist
installer run .

# Chequear versión
installer version .

# Ver logs
installer logs .

# Lanzar TUI
installer tui .

# Arrancar API
installer serve
```

---

## Verificación

```bash
# Verificar versión del ejecutable
installer --version

# Verificar ayuda
installer --help
```

---

## Configuración en pyproject.toml

```toml
[project]
name = "CLI-agent-installer"  # ← Nombre del paquete
version = "2.0.0"

[project.scripts]
installer = "cli_agent_installer.cli:main"  # ← Nombre del ejecutable
```

---

## Resumen

- ✅ Instalación: `pip install CLI-agent-installer`
- ✅ Ejecutable: `installer`
- ✅ Comandos: `installer init`, `installer run`, `installer tui`, etc.

---

*Nota: Esta aclaración es para evitar confusiones. En toda la documentación, el comando correcto es `installer`.*
