-- =====================================================================
-- PASO 1 DE LA TAREA: la vista con los 4 campos
-- Se pega y se ejecuta en Supabase -> SQL Editor
-- =====================================================================
--
-- Que hace cada parte:
--   split_part(cus.email, '@', 2)  -> de "luisg@embraer.com.br" saca "embraer.com.br"
--   split_part(  ...  , '.', 1)    -> de "embraer.com.br"       saca "embraer"
--   Ese es el "tipo de correo electronico": el proveedor (gmail, yahoo, hotmail...)
--
--   Los JOIN encadenan cliente -> factura -> detalle -> cancion -> genero,
--   porque el genero no vive en el cliente: hay que llegar a el pasando
--   por lo que el cliente compro.
--
-- Resultado: una fila por cada cancion comprada, con las 3 variables
-- independientes y la variable dependiente (genre).

DROP VIEW IF EXISTS public.train_model;

CREATE VIEW public.train_model AS
SELECT
    split_part(
        split_part(cus.email::text, '@'::text, 2),
        '.'::text,
        1
    ) AS email,
    cus.country,
    cus.city,
    gen.name AS genre
FROM
    customer cus
    JOIN invoice inv ON cus.customer_id = inv.customer_id
    JOIN invoice_line invl ON invl.invoice_id = inv.invoice_id
    JOIN track tra ON tra.track_id = invl.track_id
    JOIN genre gen ON gen.genre_id = tra.genre_id;

-- Comprobacion rapida (debe devolver 2240 filas):
-- SELECT count(*) FROM public.train_model;
-- SELECT * FROM public.train_model LIMIT 10;
