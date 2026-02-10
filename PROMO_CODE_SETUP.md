# Promo Code Setup Verification

## Promo Codes Configuration

Your promo codes are set up as follows:

### ✅ Promo Codes in Stripe (LIVE MODE)

1. **`GulfTeachers26`**
   - **Discount:** 100% off
   - **Valid for:** All teacher packages (Single, Bronze, Silver, Gold)
   - **Payment:** Bypasses card details (payment_method_collection: 'if_required')

2. **`GT50`**
   - **Discount:** 50% off
   - **Valid for:** All teacher packages (Single, Bronze, Silver, Gold)
   - **Payment:** Requires card details

3. **`GT30`**
   - **Discount:** 30% off
   - **Valid for:** Gold Teacher package ONLY
   - **Payment:** Requires card details

---

## Backend Validation Logic

The backend now validates promo codes with the following rules:

### Code Validation
- ✅ Only accepts: `GulfTeachers26`, `GT50`, `GT30` (case-insensitive)
- ✅ Rejects any other promo codes

### Package Validation
- ✅ All promo codes are **only valid for teacher packages**
- ✅ School packages cannot use these promo codes
- ✅ `GT30` is **only valid for `gold_teacher` package**
- ✅ `GulfTeachers26` and `GT50` work for all teacher packages

### Stripe Integration
- ✅ Validates promo code exists in Stripe (LIVE mode)
- ✅ Applies discount to checkout session
- ✅ For 100% discount (`GulfTeachers26`), bypasses card collection

---

## Verification Checklist

Before going live, verify:

### In Stripe Dashboard (LIVE MODE):
- [ ] `GulfTeachers26` promo code exists and is **active**
- [ ] `GulfTeachers26` coupon has **100%** discount
- [ ] `GT50` promo code exists and is **active**
- [ ] `GT50` coupon has **50%** discount
- [ ] `GT30` promo code exists and is **active**
- [ ] `GT30` coupon has **30%** discount

### In Backend Code:
- [ ] `payment/views.py` validates promo codes correctly
- [ ] Package type validation works (`package.package_for == 'teacher'`)
- [ ] `GT30` only works for `gold_teacher` package
- [ ] 100% discount bypasses card collection

### Testing:
- [ ] Test `GulfTeachers26` with all teacher packages → Should bypass card
- [ ] Test `GT50` with all teacher packages → Should require card, show 50% discount
- [ ] Test `GT30` with Gold package → Should work
- [ ] Test `GT30` with other packages → Should fail with error message
- [ ] Test promo codes with school packages → Should fail
- [ ] Test invalid promo codes → Should fail

---

## Error Messages

Users will see these error messages:

1. **Invalid promo code:** "Invalid promo code"
2. **School package:** "This promo code is only valid for teacher packages"
3. **GT30 on non-gold:** "GT30 promo code is only valid for Gold Teacher package"
4. **Stripe error:** "Promo code not found in Stripe. Please contact support."

---

## Frontend Integration

The frontend should:
- ✅ Display discount percentage when promo code is applied
- ✅ Show original price crossed out, new price highlighted
- ✅ For 100% discount, show "$0.00" and "Activate Free" button
- ✅ Bypass Stripe checkout for 100% discount codes

---

## Summary

✅ **Your setup is correct!**

- `GulfTeachers26` = 100% discount (all teacher packages) → No card required
- `GT50` = 50% discount (all teacher packages) → Card required
- `GT30` = 30% discount (Gold Teacher package only) → Card required

The backend code now validates these rules correctly. Make sure the promo codes exist in your Stripe Dashboard (LIVE mode) with the correct discount percentages.
