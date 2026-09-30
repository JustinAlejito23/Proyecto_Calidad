from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/orders", tags=["Pedidos"])

@router.post("/", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")

    total_amount = 0.0
    items_to_save = []

    try:
        for item in order_data.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto #{item.product_id} no encontrado.")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}")

            product.stock -= item.quantity
            subtotal = product.price * item.quantity
            total_amount += subtotal

            items_to_save.append({
                "product_id": product.id,
                "quantity": item.quantity,
                "unit_price": product.price
            })

        new_order = models.Order(user_id=current_user.id, total=round(total_amount, 2))
        db.add(new_order)
        db.flush()

        for item_dict in items_to_save:
            order_item = models.OrderItem(
                order_id=new_order.id,
                product_id=item_dict["product_id"],
                quantity=item_dict["quantity"],
                unit_price=item_dict["unit_price"]
            )
            db.add(order_item)

        db.commit()
        db.refresh(new_order)
        return new_order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar la compra: {str(e)}")

# ENDPOINT PARA AMPLIAR / MODIFICAR LA MISMA FACTURA
@router.put("/{order_id}", response_model=schemas.OrderOut, status_code=status.HTTP_200_OK)
def update_existing_order(
    order_id: int,
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="La factura no existe.")
    
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta factura.")

    try:
        # 1. Regresar al stock los productos que estaban antes en esta orden
        for old_item in order.items:
            prod = db.query(models.Product).filter(models.Product.id == old_item.product_id).first()
            if prod:
                prod.stock += old_item.quantity
        
        # 2. Limpiar los ítems antiguos de la orden
        db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()
        db.flush()

        # 3. Validar y descontar la nueva lista completa de productos
        total_amount = 0.0
        for item in order_data.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto #{item.product_id} no encontrado.")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}")

            product.stock -= item.quantity
            subtotal = product.price * item.quantity
            total_amount += subtotal

            new_item = models.OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price
            )
            db.add(new_item)

        order.total = round(total_amount, 2)
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando la factura: {str(e)}")