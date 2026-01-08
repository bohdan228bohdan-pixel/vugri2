# E:\soft\vugri\vugri\context_processors.py
# Малий контекст-процесор щоб показувати лічильник кошика в header
def cart_count(request):
    cart = request.session.get('cart', {}) if request else {}
    return {'cart_count': sum(int(i.get('quantity', 0)) for i in cart.values())}