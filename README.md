# Módulo de Libros Fiscales (IVA) para El Salvador

Este módulo para Odoo 18 Enterprise permite la gestión y generación de los Libros de IVA (Compras y Ventas) cumpliendo con los requerimientos del Ministerio de Hacienda de El Salvador, incluyendo soporte completo para Documentos Tributarios Electrónicos (DTE).

## Características Principales

### 1. Libro de Compras
*   **Carga Automática:** Importación de facturas de proveedor basada en el periodo fiscal seleccionado.
*   **Validación de Documentos:** Filtrado automático de tipos de documentos válidos (CCF, Notas de Crédito, etc.) y exclusión de documentos no fiscales (ej. Sujeto Excluido).
*   **Clasificación Fiscal:** Manejo de clasificaciones específicas de Hacienda (Operación, Sector, Costo/Gasto).
*   **Manejo de DTE:** Soporte nativo para campos DTE (Código de Generación, Sello de Recepción, Número de Control).
*   **Exportación:**
    *   **CSV Hacienda:** Generación de archivo CSV con el formato oficial de 21 columnas para declaración en línea (F07).
    *   **Excel:** Reporte detallado para control interno.
    *   **PDF:** Formato imprimible oficial.

### 2. Libro de Ventas (Consumidor Final y Contribuyente)
*   **Generación de Libros:** Separación automática de ventas a contribuyentes y consumidores finales.
*   **Soporte Multi-Sucursal:** Opción para consolidar ventas de todas las sucursales o filtrar por compañía.
*   **Anexos:** Generación de anexos para exportaciones y ventas a cuenta de terceros.

### 3. Cumplimiento Legal
*   **Cálculos Exactos:** Cálculo de Crédito Fiscal según reglas de Hacienda (13% exacto).
*   **Manejo de Rectificaciones:** Asistente para rectificar libros ya presentados.
*   **Validaciones:** Detección de inconsistencias antes de la exportación (NIT faltantes, tipos de documentos erróneos).

## Instrucciones de Uso

### Generar Libro de Compras
1.  Vaya al menú **Contabilidad > Informes > Libros de IVA > Libro de Compras**.
2.  Haga clic en **Nuevo**.
3.  Seleccione el **Año** y **Mes** a declarar.
4.  (Opcional) Marque "Incluir Todas las Sucursales" si desea un reporte consolidado.
5.  Haga clic en **Generar Detalle**.
    *   El sistema cargará las facturas válidas y mostrará una alerta si se omitieron documentos inválidos.
6.  Revise el detalle en la pestaña "Detalle Compras".
    *   Puede ajustar la clasificación fiscal (Costo/Gasto) si es necesario.
7.  Utilice los botones superiores para exportar:
    *   **Generar CSV:** Para subir al sistema de Hacienda.
    *   **Generar Excel:** Para revisión interna.
    *   **Imprimir PDF:** Para archivo físico.

### Generar Libro de Ventas
1.  Vaya al menú **Contabilidad > Informes > Libros de IVA > Libro de Ventas**.
2.  Siga el mismo proceso de selección de periodo.
3.  El sistema clasificará automáticamente las ventas según el tipo de cliente (Contribuyente/Consumidor).

## Requisitos Técnicos
*   Odoo 18 Enterprise
*   Módulo `l10n_sv` (Localización El Salvador)
*   Módulo de Facturación Electrónica (DTE) configurado.

## Notas de Versión
*   **v1.0:** Lanzamiento inicial con soporte para CSV F07 v21 columnas.
