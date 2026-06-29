-- dim_process_corner.sql
-- Process corner dimension (ss / tt / ff from BOMB paper)

with process_corners as (
    select distinct process_idx from {{ ref('stg_transistor_raw') }}
),

annotated as (
    select
        process_idx,
        {{ dbt_utils.generate_surrogate_key(['process_idx']) }} as process_key,

        case process_idx
            when 0 then 'Slow-Slow (ss)'
            when 1 then 'Typical-Typical (tt)'
            when 2 then 'Fast-Fast (ff)'
            else 'Unknown Corner ' || cast(process_idx as varchar)
        end as process_corner_label,

        case process_idx
            when 0 then 'SS'
            when 1 then 'TT'
            when 2 then 'FF'
            else 'UNK'
        end as process_corner_code

    from process_corners
)

select * from annotated
