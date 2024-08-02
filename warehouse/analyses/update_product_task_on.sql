CREATE TRIGGER update_product_task_on
    BEFORE UPDATE
    ON
        staging.product
    FOR EACH ROW
EXECUTE PROCEDURE update_modified_date_on_product_task();