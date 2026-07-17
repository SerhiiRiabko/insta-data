/**
 * Guest shopping cart — client-only state (localStorage) for the "Список
 * Покупок" builder (Phase 4.1). Nothing hits the backend until the user
 * presses "Створити список" (POST /api/v1/lists); until then the cart is
 * just local state that survives a page refresh.
 *
 * `session_id` is a random UUID stored alongside the cart so a created list
 * can later be attributed to "this browser" - not authentication, just the
 * anonymous-owner field Phase 4.2 (accounts) will build on.
 */

const SESSION_KEY = 'monteShopSessionId';
const CART_KEY = 'monteShopCart';

export interface CartItem {
  product_id: string;
  name: string;
  unit: string;
}

export function getSessionId(): string {
  if (typeof window === 'undefined') return '';
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function loadCart(): CartItem[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCart(items: CartItem[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CART_KEY, JSON.stringify(items));
}

export function clearCart(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(CART_KEY);
}
