INSERT INTO order_items (
    order_item_id, order_id, product_card_id,
    order_item_cardprod_id, order_item_quantity,
    order_item_product_price, order_item_discount,
    order_item_discount_rate, order_item_profit_ratio,
    sales, order_item_total
)
SELECT DISTINCT
    order_item_id, order_id, product_card_id,
    order_item_cardprod_id, order_item_quantity,
    order_item_product_price, order_item_discount,
    order_item_discount_rate, order_item_profit_ratio,
    sales, order_item_total
FROM supply_chain_data;