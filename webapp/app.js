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

function initApp() {
  try {
    const userNameEl = document.getElementById('userName');
    const profileNameEl = document.getElementById('profileName');
    const profileIdEl = document.getElementById('profileId');
    const postPhone = document.getElementById('postPhone');
    const postUsername = document.getElementById('postUsername');

    if (userNameEl) userNameEl.textContent = currentUser.first_name || 'Profil';
    if (profileNameEl) profileNameEl.textContent = currentUser.first_name || 'Foydalanuvchi';
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
  } else if (tab === 'post_ad') {
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
  const photoUrl = ad.photo_id ? `/api/photo/${ad.photo_id}` : '';
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

function openAdModal(adId) {
  const ad = allAds.find(a => a.id === adId);
  if (!ad) return;

  const photoUrl = ad.photo_id ? `/api/photo/${ad.photo_id}` : '';
  document.getElementById('modalImg').src = photoUrl;
  document.getElementById('modalTitle').textContent = `${ad.brand} ${ad.model}`;
  document.getElementById('modalPrice').textContent = ad.price;
  document.getElementById('modalMemory').textContent = ad.memory || '—';
  document.getElementById('modalCondition').textContent = ad.condition || '—';
  document.getElementById('modalBattery').textContent = ad.battery || '—';
  document.getElementById('modalColor').textContent = ad.color || '—';
  document.getElementById('modalRegion').textContent = ad.region || '—';
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

  document.getElementById('adModal').classList.add('active');
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
  const photoUrl = auc.photo_id ? `/api/photo/${auc.photo_id}` : '';
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

    const hours = Math.floor(distance / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    el.textContent = `${hours}s ${minutes}d ${seconds}sek`;
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

async function submitPostAd() {
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
    photo_id: 'default'
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
      switchBottomNav('home');
      loadAds();
    } else {
      alert('❌ Xatolik: ' + result.message);
    }
  } catch (e) {
    alert('Tarmoq xatosi yuz berdi!');
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
      const isVip = ad.is_vip ? '⭐️ VIP' : 'Oddiy';
      return `
        <div class="info-card" style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <b>${ad.brand} ${ad.model}</b>
            <div style="font-size:12px; color:var(--hint-color);">${ad.price} | ${isVip}</div>
          </div>
          <span style="font-size:12px; padding:4px 8px; border-radius:6px; background:rgba(52, 199, 89, 0.1); color:var(--success);">Faol</span>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Mening e\'lonlarimni yuklashda xatolik:', e);
  }
}
