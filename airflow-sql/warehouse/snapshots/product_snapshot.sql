{% snapshot product_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='product_id',
      strategy='timestamp',
      updated_at='modified_date',
    )
}}

select * from {{ source('adventureworks', 'product') }}

{% endsnapshot %}