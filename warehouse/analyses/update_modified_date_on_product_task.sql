CREATE  FUNCTION update_modified_date_on_product_task()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_date = now();
    RETURN NEW;
END;
$$ language 'plpgsql';