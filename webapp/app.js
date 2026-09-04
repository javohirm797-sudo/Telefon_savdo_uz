// Telegram Web App SDK
const tg = window.Telegram?.WebApp;
try {
  if (tg) {
    tg.ready();
    tg.expand();
  }
} catch (e) {
  console.warn("Telegram SDK xatosi:", e);
}

let allAds = [];
let filteredAds = [];
let allAuctions = [];
let currentBrand = 'all';
let currentRegion = 'all';
let searchQuery = '';
let selectedAuction = null;
let countdownTimer = null;

// Foydalanuvchi ma'lumotlari
const currentUser = tg?.initDataUnsafe?.user || {
  id: 8530025653,
  first_name: "Mehmon",
  username: "user"
};

function formatAdDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr).substring(0, 16);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}.${month}.${year} ${hours}:${minutes}`;
  } catch (e) {
    return String(dateStr).substring(0, 16);
  }
}

function initApp() {
  try {
    const userNameEl = document.getElementById('userName');
    const profileNameEl = document.getElementById('profileName');
    const profileUsernameEl = document.getElementById('profileUsername');
    const profileIdEl = document.getElementById('profileId');
    const postPhone = document.getElementById('postPhone');
    const postUsername = document.getElementById('postUsername');

    const fullName = [currentUser.first_name, currentUser.last_name].filter(Boolean).join(' ') || 'Foydalanuvchi';
    if (userNameEl) userNameEl.textContent = currentUser.first_name || 'Profil';
    if (profileNameEl) profileNameEl.textContent = fullName;
    if (profileUsernameEl) {
      profileUsernameEl.textContent = currentUser.username ? `@${currentUser.username}` : '—';
    }
    if (profileIdEl) profileIdEl.textContent = `ID: ${currentUser.id}`;
    if (postUsername && currentUser.username) postUsername.value = `@${currentUser.username}`;
  } catch (err) {
    console.error("DOM xatosi:", err);
  }

  loadAds();
  loadAuctions();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// ==================== BOTTOM NAVIGATION (PASTKI MENYU) ====================

function switchBottomNav(tab) {
  // Barcha view larni yashirish
  document.querySelectorAll('.app-view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.app-view').forEach(v => v.style.display = 'none');
  
  // Barcha nav item lardan active ni olib tashlash
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  if (tab === 'home') {
    const view = document.getElementById('viewHome');
    view.style.display = 'block';
    view.classList.add('active');
    document.getElementById('navHome').classList.add('active');
    switchTab('market');
  } else if (tab === 'auction') {
    const view = document.getElementById('viewHome');
    view.style.display = 'block';
    view.classList.add('active');
    document.getElementById('navAuction').classList.add('active');
    switchTab('auction');
  } else if (tab === 'post_ad' || tab === 'post') {
    const view = document.getElementById('viewPostAd');
    view.style.display = 'block';
    view.classList.add('active');
    document.getElementById('navPost').classList.add('active');
  } else if (tab === 'info') {
    const view = document.getElementById('viewInfo');
    view.style.display = 'block';
    view.classList.add('active');
    document.getElementById('navInfo').classList.add('active');
  } else if (tab === 'profile') {
    const view = document.getElementById('viewProfile');
    view.style.display = 'block';
    view.classList.add('active');
    document.getElementById('navProfile').classList.add('active');
    loadMyAds();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==================== BOZOR E'LONLARI ====================

async function loadAds() {
  const spinner = document.getElementById('loadingSpinner');
  const emptyState = document.getElementById('emptyState');
  const adsGrid = document.getElementById('adsGrid');
  const countBadge = document.getElementById('adsCount');

  // Zagruzka spinneri hech qachon 2.5 soniyadan ortiq aylanmaydi (qotib qolishni yo'qotadi)
  const forceHideSpinner = setTimeout(() => {
    if (spinner) spinner.style.display = 'none';
  }, 2500);

  try {
    const res = await fetch('/api/ads');
    allAds = await res.json();
    clearTimeout(forceHideSpinner);
    if (spinner) spinner.style.display = 'none';
    applyFilters();
  } catch (err) {
    console.error('E\'lonlarni yuklashda xatolik:', err);
    clearTimeout(forceHideSpinner);
    if (spinner) spinner.style.display = 'none';
    if (countBadge) countBadge.textContent = 'Qayta urinib ko\'ring';
  }
}

function applyFilters() {
  const adsGrid = document.getElementById('adsGrid');
  const emptyState = document.getElementById('emptyState');
  const countBadge = document.getElementById('adsCount');

  filteredAds = allAds.filter(ad => {
    const matchBrand = (currentBrand === 'all') || (ad.brand?.toLowerCase() === currentBrand.toLowerCase());
    const matchRegion = (currentRegion === 'all') || (ad.region === currentRegion || ad.region?.includes(currentRegion));
    const query = searchQuery.toLowerCase().trim();
    const matchQuery = !query || 
      ad.model?.toLowerCase().includes(query) || 
      ad.brand?.toLowerCase().includes(query) || 
      ad.description?.toLowerCase().includes(query);
    return matchBrand && matchRegion && matchQuery;
  });

  if (countBadge) countBadge.textContent = `${filteredAds.length} ta telefon topildi`;

  if (filteredAds.length === 0) {
    if (adsGrid) adsGrid.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  if (adsGrid) adsGrid.innerHTML = filteredAds.map(ad => renderAdCard(ad)).join('');
}

function renderAdCard(ad) {
  const isVip = ad.is_vip ? 'vip' : '';
  const vipBadge = ad.is_vip ? '<span class="card-vip-badge">⭐️ VIP</span>' : '';
  const photoUrl = ad.photo_id ? `/api/photo/${ad.photo_id}?v=real` : '';
  const title = `${ad.brand || ''} ${ad.model || ''}`;

  return `
    <div class="ad-card ${isVip}" onclick="openAdModal(${ad.id})">
      <div class="ad-thumb-wrap">
        <img class="ad-thumb" src="${photoUrl}" alt="${title}" loading="lazy">
        ${vipBadge}
      </div>
      <div class="card-info">
        <div class="card-price">${ad.price || 'Kelishiladi'}</div>
        <div class="card-title">${title}</div>
        <div class="card-meta">
          <span>${ad.memory || ''}</span>
          <span>${ad.region || ''}</span>
        </div>
        ${ad.created_at ? `<div class="card-date" style="font-size:11px; color:var(--hint-color); margin-top:4px;"><i class="fa-regular fa-clock"></i> ${formatAdDate(ad.created_at)}</div>` : ''}
      </div>
    </div>
  `;
}

// Brend bo'yicha filter
function filterByBrand(brand, el) {
  currentBrand = brand;
  document.querySelectorAll('.brand-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  applyFilters();
}

// Qidiruv
function onSearchInput() {
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearch');
  searchQuery = input.value;
  clearBtn.style.display = searchQuery ? 'block' : 'none';
  applyFilters();
}

function clearSearch() {
  const input = document.getElementById('searchInput');
  input.value = '';
  searchQuery = '';
  document.getElementById('clearSearch').style.display = 'none';
  applyFilters();
}

// ==================== MODAL OYNA (E'lon tafsilotlari) ====================

let currentOpenedAdId = null;

function openAdModal(adId) {
  const ad = allAds.find(a => a.id === adId);
  if (!ad) return;

  currentOpenedAdId = adId;

  const photoUrl = ad.photo_id ? `/api/photo/${ad.photo_id}?v=real` : '';
  document.getElementById('modalImg').src = photoUrl;
  document.getElementById('modalTitle').textContent = `${ad.brand} ${ad.model}`;
  document.getElementById('modalPrice').textContent = ad.price;
  document.getElementById('modalMemory').textContent = ad.memory || '—';
  document.getElementById('modalCondition').textContent = ad.condition || '—';
  document.getElementById('modalBattery').textContent = ad.battery || '—';
  document.getElementById('modalColor').textContent = ad.color || '—';
  document.getElementById('modalRegion').textContent = ad.region || '—';
  
  const createdAtEl = document.getElementById('modalCreatedAt');
  if (createdAtEl) createdAtEl.textContent = formatAdDate(ad.created_at) || 'Yaqinda';

  document.getElementById('modalDesc').textContent = ad.description || 'Qo\'shimcha ma\'lumot berilmagan.';

  const vipBadge = document.getElementById('modalVipBadge');
  vipBadge.style.display = ad.is_vip ? 'block' : 'none';

  // Aloqa tugmalari
  const tgLink = document.getElementById('modalTgLink');
  if (ad.contact_username) {
    const user = ad.contact_username.replace('@', '');
    tgLink.href = `https://t.me/${user}`;
    tgLink.style.display = 'flex';
  } else {
    tgLink.style.display = 'none';
  }

  const phoneLink = document.getElementById('modalPhoneLink');
  if (ad.contact_phone) {
    phoneLink.href = `tel:${ad.contact_phone}`;
    phoneLink.style.display = 'flex';
  } else {
    phoneLink.style.display = 'none';
  }

  // Admin uchun e'lonni o'chirish tugmasi
  const adminDelRow = document.getElementById('modalAdminDeleteRow');
  if (adminDelRow) {
    const ADMIN_IDS = [8530025653];
    if (ADMIN_IDS.includes(Number(currentUser.id))) {
      adminDelRow.style.display = 'block';
    } else {
      adminDelRow.style.display = 'none';
    }
  }

  document.getElementById('adModal').classList.add('active');
}

async function adminDeleteCurrentAd() {
  if (!currentOpenedAdId) return;
  if (!confirm("Admin: Haqiqatan ham ushbu e'lonni o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch('/api/delete_ad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ad_id: currentOpenedAdId, user_id: currentUser.id })
    });
    const result = await res.json();
    if (result.success) {
      alert('✅ ' + result.message);
      closeModalDirect();
      loadAds();
    } else {
      alert('❌ ' + result.message);
    }
  } catch (e) {
    alert('Aloqa xatosi yuz berdi!');
  }
}

function closeModal(e) {
  if (e.target.id === 'adModal') closeModalDirect();
}

function closeModalDirect() {
  document.getElementById('adModal').classList.remove('active');
}

// ==================== KIMOSHDI (AUKSION) ====================

async function loadAuctions() {
  try {
    const res = await fetch('/api/auctions');
    allAuctions = await res.json();
    renderAuctions();
  } catch (err) {
    console.error('Auksionlarni yuklashda xatolik:', err);
  }
}

function renderAuctions() {
  const list = document.getElementById('auctionsList');
  const emptyState = document.getElementById('emptyAuctionState');
  const countBadge = document.getElementById('auctionsCount');

  const filteredAuctions = allAuctions.filter(auc => {
    return (currentRegion === 'all') || (auc.region === currentRegion || auc.region?.includes(currentRegion));
  });

  if (countBadge) countBadge.textContent = `${filteredAuctions.length} ta faol auksion`;

  if (filteredAuctions.length === 0) {
    if (list) list.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  if (list) list.innerHTML = filteredAuctions.map(auc => renderAuctionCard(auc)).join('');
  startAuctionTimers();
}

// Hudud (Viloyat) o'zgarganda
function onRegionChange(region) {
  currentRegion = region;
  const reg1 = document.getElementById('regionSelect');
  const reg2 = document.getElementById('auctionRegionSelect');
  if (reg1) reg1.value = region;
  if (reg2) reg2.value = region;

  applyFilters();
  renderAuctions();
}

function renderAuctionCard(auc) {
  const photoUrl = auc.photo_id ? `/api/photo/${auc.photo_id}?v=real` : '';
  const title = `${auc.brand} ${auc.model}`;
  const currPrice = (auc.current_price || auc.start_price || 0).toLocaleString();
  const minStep = (auc.min_step || 50000).toLocaleString();
  const winner = auc.current_winner_name || 'Hali taklif yo\'q';

  return `
    <div class="auction-card">
      <div class="auc-header">
        <img class="auc-img" src="${photoUrl}" alt="${title}">
        <div class="auc-timer" id="timer-${auc.id}">
          <i class="fa-regular fa-clock"></i> <span>Hisoblanmoqda...</span>
        </div>
      </div>
      <div class="auc-body">
        <div class="auc-title">${title} (${auc.memory || ''})</div>
        <div class="auc-price-row">
          <div>
            <div class="auc-price-label">Eng yuqori taklif:</div>
            <div class="auc-price-val">${currPrice} so'm</div>
          </div>
          <div style="text-align: right;">
            <div class="auc-price-label">Yetakchi:</div>
            <b style="font-size: 13px;">${winner}</b>
          </div>
        </div>
        <button class="auc-bid-btn" onclick="openBidModal(${auc.id})">
          <i class="fa-solid fa-hand-holding-dollar"></i> Stavka qo'yish (+${minStep} so'm)
        </button>
      </div>
    </div>
  `;
}

function startAuctionTimers() {
  if (countdownTimer) clearInterval(countdownTimer);
  updateTimers();
  countdownTimer = setInterval(updateTimers, 1000);
}

function updateTimers() {
  const now = new Date().getTime();
  allAuctions.forEach(auc => {
    const el = document.querySelector(`#timer-${auc.id} span`);
    if (!el) return;

    const endTime = new Date(auc.end_time).getTime();
    const distance = endTime - now;

    if (distance < 0) {
      el.textContent = 'Auksion tugadi';
      return;
    }

    const totalHours = Math.floor(distance / (1000 * 60 * 60));
    const hours = String(totalHours).padStart(2, '0');
    const minutes = String(Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))).padStart(2, '0');
    const seconds = String(Math.floor((distance % (1000 * 60)) / 1000)).padStart(2, '0');

    el.textContent = `${hours}:${minutes}:${seconds}`;
  });
}

// ==================== STAVKA BERISH MODALI ====================

function openBidModal(aucId) {
  selectedAuction = allAuctions.find(a => a.id === aucId);
  if (!selectedAuction) return;

  const title = `${selectedAuction.brand} ${selectedAuction.model}`;
  const currPrice = selectedAuction.current_price || selectedAuction.start_price;
  const minStep = selectedAuction.min_step || 50000;
  const nextMinBid = selectedAuction.current_winner_id ? currPrice + minStep : currPrice;

  document.getElementById('bidAuctionTitle').textContent = title;
  document.getElementById('bidCurrentPrice').textContent = `${currPrice.toLocaleString()} so'm`;
  document.getElementById('bidMinStep').textContent = `+${minStep.toLocaleString()} so'm`;
  
  const input = document.getElementById('bidAmountInput');
  input.value = nextMinBid;
  input.min = nextMinBid;

  const quickBox = document.getElementById('quickBidButtons');
  quickBox.innerHTML = `
    <button class="quick-btn" onclick="setBidAmount(${nextMinBid})">${nextMinBid.toLocaleString()} so'm</button>
    <button class="quick-btn" onclick="setBidAmount(${nextMinBid + minStep})">${(nextMinBid + minStep).toLocaleString()} so'm</button>
  `;

  document.getElementById('bidModal').classList.add('active');
}

function setBidAmount(amount) {
  document.getElementById('bidAmountInput').value = amount;
}

function closeBidModal(e) {
  if (e.target.id === 'bidModal') closeBidModalDirect();
}

function closeBidModalDirect() {
  document.getElementById('bidModal').classList.remove('active');
}

async function submitBid() {
  if (!selectedAuction) return;
  const amount = parseInt(document.getElementById('bidAmountInput').value);
  if (!amount) {
    alert('Iltimos, stavka summasini kiriting!');
    return;
  }

  try {
    const res = await fetch('/api/bid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auction_id: selectedAuction.id,
        user_id: currentUser.id,
        user_name: currentUser.first_name || 'Xaridor',
        bid_amount: amount
      })
    });
    const result = await res.json();
    if (result.success) {
      alert('✅ ' + result.message);
      closeBidModalDirect();
      loadAuctions();
    } else {
      alert('❌ ' + result.message);
    }
  } catch (err) {
    alert('Aloqa xatosi yuz berdi.');
  }
}

// ==================== TAB SWITCHING (Bozor / Auksion) ====================

function switchTab(tab) {
  const marketTab = document.getElementById('tabMarket');
  const auctionTab = document.getElementById('tabAuction');
  const marketSection = document.getElementById('marketSection');
  const auctionSection = document.getElementById('auctionSection');
  const brandsWrapper = document.getElementById('brandsWrapper');
  const searchBox = document.querySelector('.search-box');

  if (tab === 'market') {
    marketTab.classList.add('active');
    auctionTab.classList.remove('active');
    marketSection.style.display = 'block';
    auctionSection.style.display = 'none';
    brandsWrapper.style.display = 'flex';
    searchBox.style.display = 'flex';
  } else {
    auctionTab.classList.add('active');
    marketTab.classList.remove('active');
    marketSection.style.display = 'none';
    auctionSection.style.display = 'block';
    brandsWrapper.style.display = 'none';
    searchBox.style.display = 'none';
    loadAuctions();
  }
}

// ==================== E'LON BERISH (FORM SUBMIT) ====================

// ==================== RASM YUKLASH & SIQISH (COMPRESSION) ====================

let selectedPhotoBase64 = null;

function compressImage(file, callback) {
  const reader = new FileReader();
  reader.onload = function(e) {
    const img = new Image();
    img.onload = function() {
      const canvas = document.createElement('canvas');
      let width = img.width;
      let height = img.height;
      const maxSide = 1024;
      if (width > maxSide || height > maxSide) {
        if (width > height) {
          height = Math.round((height * maxSide) / width);
          width = maxSide;
        } else {
          width = Math.round((width * maxSide) / height);
          height = maxSide;
        }
      }
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);
      callback(canvas.toDataURL('image/jpeg', 0.85));
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function onPhotoSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  compressImage(file, function(base64) {
    selectedPhotoBase64 = base64;
    document.getElementById('postPhotoPreview').src = base64;
    document.getElementById('photoUploadTrigger').style.display = 'none';
    document.getElementById('postPhotoPreviewWrapper').style.display = 'block';
  });
}

function removeSelectedPhoto() {
  selectedPhotoBase64 = null;
  const input = document.getElementById('postPhotoInput');
  if (input) input.value = '';
  const preview = document.getElementById('postPhotoPreviewWrapper');
  const trigger = document.getElementById('photoUploadTrigger');
  if (preview) preview.style.display = 'none';
  if (trigger) trigger.style.display = 'flex';
}

// ==================== E'LON BERISH (FORM SUBMIT) ====================

let isPostSubmitting = false;

async function submitPostAd() {
  if (isPostSubmitting) return;

  const brand = document.getElementById('postBrand').value;
  const model = document.getElementById('postModel').value.trim();
  const memory = document.getElementById('postMemory').value;
  const condition = document.getElementById('postCondition').value;
  const price = document.getElementById('postPrice').value.trim();
  const battery = document.getElementById('postBattery').value.trim() || '—';
  const color = document.getElementById('postColor').value.trim() || '—';
  const region = document.getElementById('postRegion').value;
  const phone = document.getElementById('postPhone').value.trim();
  const username = document.getElementById('postUsername').value.trim();
  const desc = document.getElementById('postDesc').value.trim();

  if (!model) {
    alert('Iltimos, telefon modelini kiriting!');
    return;
  }
  if (!price) {
    alert('Iltimos, telefon narxini kiriting!');
    return;
  }
  if (!phone) {
    alert('Iltimos, telefon raqamingizni kiriting!');
    return;
  }

  const submitBtn = document.querySelector('#viewPostAd .primary-submit-btn');
  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> E\'lon chop etilmoqda...';
  }
  isPostSubmitting = true;

  const payload = {
    user_id: currentUser.id,
    brand: brand,
    model: model,
    memory: memory,
    condition: condition,
    price: price,
    battery: battery,
    color: color,
    region: region,
    contact_phone: phone,
    contact_username: username,
    description: desc,
    photo_base64: selectedPhotoBase64 || ''
  };

  try {
    const res = await fetch('/api/post_ad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert('🎉 E\'loningiz muvaffaqiyatli joylandi!');
      // Formani tozalash
      document.getElementById('postModel').value = '';
      document.getElementById('postPrice').value = '';
      document.getElementById('postDesc').value = '';
      removeSelectedPhoto();
      switchBottomNav('home');
      loadAds();
    } else {
      alert('❌ Xatolik: ' + result.message);
    }
  } catch (e) {
    alert('Tarmoq xatosi yuz berdi!');
  } finally {
    isPostSubmitting = false;
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
  }
}

// ==================== POST TYPE SWITCHER (ODDIY / AUKSION) ====================
let currentPostType = 'normal';
let selectedAucReceiptBase64 = null;

function switchPostType(type) {
  currentPostType = type;
  const btnNormal = document.getElementById('btnTypeNormal');
  const btnAuction = document.getElementById('btnTypeAuction');
  const normalPriceRow = document.getElementById('normalPriceRow');
  const auctionFieldsGroup = document.getElementById('auctionFieldsGroup');
  const btnSubmitAd = document.getElementById('btnSubmitAd');
  const btnSubmitAuction = document.getElementById('btnSubmitAuction');
  const formTitle = document.getElementById('postFormTitle');
  const formSub = document.getElementById('postFormSub');

  if (type === 'auction') {
    if (btnNormal) {
      btnNormal.style.background = 'transparent';
      btnNormal.style.color = 'var(--hint-color)';
    }
    if (btnAuction) {
      btnAuction.style.background = 'linear-gradient(135deg, #ff9500, #ff5e3a)';
      btnAuction.style.color = '#fff';
    }
    if (normalPriceRow) normalPriceRow.style.display = 'none';
    if (auctionFieldsGroup) auctionFieldsGroup.style.display = 'block';
    if (btnSubmitAd) btnSubmitAd.style.display = 'none';
    if (btnSubmitAuction) btnSubmitAuction.style.display = 'block';
    if (formTitle) formTitle.innerHTML = '<i class="fa-solid fa-gavel"></i> Auksionga telefon qo\'yish';
    if (formSub) formSub.textContent = 'Eng yuqori narxda sotish uchun auksion e\'loni bering';
  } else {
    if (btnNormal) {
      btnNormal.style.background = 'var(--primary-accent)';
      btnNormal.style.color = '#fff';
    }
    if (btnAuction) {
      btnAuction.style.background = 'transparent';
      btnAuction.style.color = 'var(--hint-color)';
    }
    if (normalPriceRow) normalPriceRow.style.display = 'flex';
    if (auctionFieldsGroup) auctionFieldsGroup.style.display = 'none';
    if (btnSubmitAd) btnSubmitAd.style.display = 'block';
    if (btnSubmitAuction) btnSubmitAuction.style.display = 'none';
    if (formTitle) formTitle.textContent = '➕ Yangi e\'lon joylash';
    if (formSub) formSub.textContent = 'Telefoningizni tez va qulay soting';
  }
}

function goToPostAuction() {
  switchBottomNav('post_ad');
  switchPostType('auction');
}

function copyCardNumber() {
  const card = "5614681875921300";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(card).then(() => {
      alert("✅ Karta raqami nusxalandi: 5614 6818 7592 1300");
    }).catch(() => {
      prompt("Karta raqamini nusxalab oling:", card);
    });
  } else {
    prompt("Karta raqamini nusxalab oling:", card);
  }
}

function onAucReceiptSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  compressImage(file, function(base64) {
    selectedAucReceiptBase64 = base64;
    const preview = document.getElementById('aucReceiptPreview');
    const wrap = document.getElementById('aucReceiptPreviewWrap');
    const trigger = document.getElementById('aucReceiptTrigger');
    if (preview) preview.src = base64;
    if (wrap) wrap.style.display = 'block';
    if (trigger) trigger.style.display = 'none';
  });
}

function removeAucReceiptPhoto() {
  selectedAucReceiptBase64 = null;
  const input = document.getElementById('postAucReceiptInput');
  if (input) input.value = '';
  const wrap = document.getElementById('aucReceiptPreviewWrap');
  const trigger = document.getElementById('aucReceiptTrigger');
  if (wrap) wrap.style.display = 'none';
  if (trigger) trigger.style.display = 'block';
}

async function submitPostAuction() {
  if (isPostSubmitting) return;

  const brand = document.getElementById('postBrand').value;
  const model = document.getElementById('postModel').value.trim();
  const memory = document.getElementById('postMemory').value;
  const condition = document.getElementById('postCondition').value;
  const battery = (document.getElementById('postAucBattery') ? document.getElementById('postAucBattery').value.trim() : '') || '—';
  const color = document.getElementById('postColor').value.trim() || '—';
  const region = document.getElementById('postRegion').value;
  const phone = document.getElementById('postPhone').value.trim();
  const username = document.getElementById('postUsername').value.trim();
  const desc = document.getElementById('postDesc').value.trim();

  const startPrice = parseInt(document.getElementById('postAucStartPrice').value) || 0;
  const minStep = parseInt(document.getElementById('postAucMinStep').value) || 50000;
  const duration = parseInt(document.getElementById('postAucDuration').value) || 24;

  if (!model) {
    alert('Iltimos, telefon modelini kiriting!');
    return;
  }
  if (!startPrice || startPrice < 10000) {
    alert('Iltimos, to\'g\'ri boshlang\'ich narx kiriting (kamida 10 000 so\'m)!');
    return;
  }
  if (!phone) {
    alert('Iltimos, telefon raqamingizni kiriting!');
    return;
  }
  if (!selectedPhotoBase64) {
    alert('Iltimos, telefoningiz rasmini yuklang!');
    return;
  }
  if (!selectedAucReceiptBase64) {
    alert('Iltimos, 5 000 so\'m auksion to\'lovi chekining skrinshotini yuklang!');
    return;
  }

  const submitBtn = document.getElementById('btnSubmitAuction');
  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Auksion yuborilmoqda...';
  }
  isPostSubmitting = true;

  const payload = {
    user_id: currentUser.id,
    brand: brand,
    model: model,
    memory: memory,
    condition: condition,
    battery: battery,
    color: color,
    region: region,
    contact_phone: phone,
    contact_username: username,
    description: desc,
    start_price: startPrice,
    min_step: minStep,
    duration_hours: duration,
    photo_base64: selectedPhotoBase64,
    receipt_base64: selectedAucReceiptBase64
  };

  try {
    const res = await fetch('/api/post_auction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert('🎉 Auksion so\'rovingiz muvaffaqiyatli qabul qilindi!\n\nAdmin to\'lov chekini tekshirib tasdiqlashi bilan auksion boshlanadi va sizga xabar beriladi.');
      // Tozalash
      document.getElementById('postModel').value = '';
      document.getElementById('postDesc').value = '';
      if (document.getElementById('postAucStartPrice')) document.getElementById('postAucStartPrice').value = '';
      removeSelectedPhoto();
      removeAucReceiptPhoto();
      switchPostType('normal');
      switchBottomNav('home');
      switchMainTab('auctions');
      loadAuctions();
    } else {
      alert('❌ Xatolik: ' + result.message);
    }
  } catch (e) {
    alert('Tarmoq xatosi yuz berdi!');
  } finally {
    isPostSubmitting = false;
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
  }
}

// ==================== PROFIL: MENING E'LONLARIM ====================

async function loadMyAds() {
  const listEl = document.getElementById('myAdsList');
  const countEl = document.getElementById('myAdsCount');

  try {
    const res = await fetch(`/api/my_ads?user_id=${currentUser.id}`);
    const myAds = await res.json();
    countEl.textContent = myAds.length;

    if (myAds.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-folder-open"></i>
          <p>Sizda hali e'lonlar mavjud emas.</p>
        </div>
      `;
      return;
    }

    listEl.innerHTML = myAds.map(ad => {
      const isVipBadge = ad.is_vip ? '<span class="card-vip-badge">⭐️ VIP</span>' : '';
      const adTitle = `${ad.brand} ${ad.model}`.replace(/'/g, "\\'");
      return `
        <div class="my-ad-card">
          <div class="my-ad-top">
            <div>
              <div class="my-ad-title">${ad.brand} ${ad.model}</div>
              <div class="my-ad-meta">${ad.memory || ''} | ${ad.condition || ''} | ${ad.region || ''}</div>
              <div class="my-ad-price">${ad.price}</div>
            </div>
            ${isVipBadge}
          </div>
          <div class="my-ad-actions">
            ${!ad.is_vip ? `<button type="button" class="btn-my-ad btn-vip-ad" onclick="openVipModal(${ad.id}, '${adTitle}')"><i class="fa-solid fa-crown"></i> VIP qilish</button>` : ''}
            <button type="button" class="btn-my-ad btn-delete-ad" onclick="deleteMyAd(${ad.id})"><i class="fa-solid fa-trash-can"></i> O'chirish</button>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Mening e\'lonlarimni yuklashda xatolik:', e);
  }
}

async function deleteMyAd(adId) {
  if (!confirm("Haqiqatan ham ushbu e'lonni o'chirmoqchimisiz?")) return;
  try {
    const res = await fetch('/api/delete_ad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ad_id: adId, user_id: currentUser.id })
    });
    const result = await res.json();
    if (result.success) {
      alert('✅ ' + result.message);
      loadMyAds();
      loadAds();
    } else {
      alert('❌ ' + result.message);
    }
  } catch (err) {
    alert('Aloqa xatosi yuz berdi!');
  }
}

// ==================== VIP MODAL VA TO'LOV LOGIKASI ====================

let selectedVipAdId = null;
let selectedVipPlanDays = 1;
let selectedVipReceiptBase64 = null;

function openVipModal(adId, title) {
  selectedVipAdId = adId;
  selectedVipPlanDays = 1;
  selectedVipReceiptBase64 = null;
  removeReceiptPhoto();
  selectVipPlan(1, 5000);
  document.getElementById('vipAdTitle').textContent = `E'lon: ${title}`;
  document.getElementById('vipModal').classList.add('active');
}

function closeVipModal(e) {
  if (e.target.id === 'vipModal') closeVipModalDirect();
}

function closeVipModalDirect() {
  document.getElementById('vipModal').classList.remove('active');
}

function selectVipPlan(days, amount) {
  selectedVipPlanDays = days;
  document.querySelectorAll('.vip-plan-card').forEach(c => c.classList.remove('active'));
  const el = document.getElementById(`plan${days}`);
  if (el) el.classList.add('active');
}

function copyCardNumber() {
  const cardNum = '5614681875921300';
  if (navigator.clipboard) {
    navigator.clipboard.writeText(cardNum).then(() => {
      alert('✅ Karta raqami nusxalandi: 5614-6818-7592-1300');
    }).catch(() => {
      alert('Karta raqami: 5614-6818-7592-1300');
    });
  } else {
    alert('Karta raqami: 5614-6818-7592-1300');
  }
}

function onReceiptSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  compressImage(file, function(base64) {
    selectedVipReceiptBase64 = base64;
    document.getElementById('receiptPreviewImg').src = base64;
    document.getElementById('receiptUploadTrigger').style.display = 'none';
    document.getElementById('receiptPreviewWrap').style.display = 'block';
  });
}

function removeReceiptPhoto() {
  selectedVipReceiptBase64 = null;
  const input = document.getElementById('vipReceiptInput');
  if (input) input.value = '';
  const preview = document.getElementById('receiptPreviewWrap');
  const trigger = document.getElementById('receiptUploadTrigger');
  if (preview) preview.style.display = 'none';
  if (trigger) trigger.style.display = 'flex';
}

async function submitVipPayment() {
  if (!selectedVipAdId) return;
  if (!selectedVipReceiptBase64) {
    alert('Iltimos, to\'lov cheki skrinshotini yuklang!');
    return;
  }

  try {
    const res = await fetch('/api/buy_vip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ad_id: selectedVipAdId,
        user_id: currentUser.id,
        plan_days: selectedVipPlanDays,
        receipt_base64: selectedVipReceiptBase64
      })
    });
    const result = await res.json();
    if (result.success) {
      alert('🎉 ' + result.message);
      closeVipModalDirect();
      loadMyAds();
    } else {
      alert('❌ Xatolik: ' + result.message);
    }
  } catch (err) {
    alert('Aloqa xatosi yuz berdi!');
  }
}
