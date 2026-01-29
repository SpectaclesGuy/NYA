const API_BASE = window.location.origin;

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  const opts = {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  const response = await fetch(`${API_BASE}${path}`, opts);
  if (response.status === 401) {
    window.location.href = '/authentication';
    throw new Error('unauthorized');
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const base = data?.error?.message || 'Request failed';
    const details = data?.error?.details ? ` (${data.error.details})` : '';
    const message = `${base}${details}`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

function createSkillChips(skills) {
  return skills
    .map((skill) => `<span class="skill-chip border-gray-300 text-[10px] uppercase font-semibold px-3 py-2 text-gray-600">${skill}</span>`)
    .join('');
}

function getAvatarUrl(seed) {
  const avatars = [
    '/assets/default_avatar.svg',
    '/assets/default_avatar_2.svg',
    '/assets/default_avatar_3.svg',
    '/assets/default_avatar_4.svg',
    '/assets/default_avatar_5.svg',
    '/assets/default_avatar_6.svg',
    '/assets/default_avatar_7.svg',
    '/assets/default_avatar_8.svg',
    '/assets/default_avatar_9.svg',
  ];
  if (!seed) {
    return avatars[0];
  }
  const text = String(seed);
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash + text.charCodeAt(i)) % avatars.length;
  }
  return avatars[hash];
}

function initFontLoading() {
  const root = document.documentElement;
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => {
      root.classList.add('fonts-loaded');
    });
  } else {
    root.classList.add('fonts-loaded');
  }
}

async function initOnboardingGuard() {
  const path = window.location.pathname;
  const publicPaths = [
    '/',
    '/landing',
    '/transition',
    '/main_dashboard',
    '/authentication',
    '/onboarding/role',
    '/profile/setup',
    '/mentor/setup',
  ];
  if (publicPaths.includes(path)) {
    return;
  }

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN') {
      return;
    }
    if (!status.role_selected) {
      window.location.href = '/onboarding/role';
      return;
    }
    if (status.role === 'MENTOR') {
      if (!status.has_profile) {
        window.location.href = '/mentor/setup';
        return;
      }
      if (!status.mentor_approved && path !== '/mentor/pending') {
        window.location.href = '/mentor/pending';
      }
      return;
    }
    if (!status.has_profile) {
      window.location.href = '/profile/setup';
    }
  } catch (error) {
    // ignore
  }
}

async function initGlobalNav() {
  if (
    window.location.pathname === '/authentication'
    || window.location.pathname === '/'
    || window.location.pathname === '/landing'
    || window.location.pathname === '/transition'
    || window.location.pathname === '/main_dashboard'
  ) {
    return;
  }
  const nameEl = document.getElementById('nav-user-name');
  const profileLink = document.getElementById('nav-profile-link');
  const adminLink = document.getElementById('admin-nav');
  const mentorLink = document.getElementById('mentor-nav');
  const adminLinks = document.querySelectorAll('[data-nav-id="admin-nav"]');
  const mentorLinks = document.querySelectorAll('[data-nav-id="mentor-nav"]');
  const welcomeName = document.getElementById('welcome-name');
  if (!nameEl && !profileLink && !adminLink && !mentorLink && !welcomeName) {
    return;
  }

  try {
    const me = await apiFetch('/api/users/me');
    if (nameEl && me?.name) {
      nameEl.textContent = me.name;
    }
    if (welcomeName && me?.name) {
      welcomeName.textContent = me.name.split(' ')[0];
    }
    if (profileLink && me?.id) {
      profileLink.href = `/profile?user_id=${me.id}`;
    }
    if (me?.role === 'ADMIN') {
      if (adminLink) {
        adminLink.classList.remove('hidden');
      }
      adminLinks.forEach((link) => link.classList.remove('hidden'));
    }
  } catch (error) {
    // ignore
  }

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN' && adminLink) {
      adminLink.classList.remove('hidden');
    }
    if (status.role === 'MENTOR' && status.mentor_approved && mentorLink) {
      mentorLink.classList.remove('hidden');
    }
    if (status.role === 'ADMIN') {
      adminLinks.forEach((link) => link.classList.remove('hidden'));
    }
    if (status.role === 'MENTOR' && status.mentor_approved) {
      mentorLinks.forEach((link) => link.classList.remove('hidden'));
    }
  } catch (error) {
    // ignore
  }
}

async function initMainDashboardStories() {
  const container = document.getElementById('lead-stories');
  const prevButton = document.getElementById('story-prev');
  const nextButton = document.getElementById('story-next');
  if (!container) {
    return;
  }
  const fallback = [
    {
      title: 'The Big Boy on The Sofa',
      image: '/assets/yooo.jpeg',
      description: 'A new wave of capstone leaders are forming circles across the community.',
      link: '/mentors',
    },
    {
      title: 'Mentor Dispatch',
      image: '/assets/nya_logo_nobg.png',
      description: 'Freshly approved prefects are live with focus areas and availability.',
      link: '/mentor/dashboard',
    },
    {
      title: 'Project Pulse',
      image: '/assets/nya_logo_nobg.png',
      description: 'Teams are assembling across product, AI, and design for the next sprint.',
      link: '/dashboard',
    },
    {
      title: 'Studio Open Calls',
      image: '/assets/nya_logo_nobg.png',
      description: 'Track hackathon openings and align with deadlines before you commit.',
      link: '/hackathons',
    },
  ];
  let stories = fallback.slice();
  let currentIndex = 0;
  let rotationTimer = null;

  const render = () => {
    const current = stories[currentIndex] || stories[0];
    container.innerHTML = current
      ? `
        <div class="story-swap space-y-6">
        <a href="${current.link || '/mentors'}" class="headline-link inline-flex w-full justify-center">
          <h3 class="headline-title text-4xl text-primary text-center w-full">${current.title}</h3>
        </a>
          <div class="border border-warm-gray aspect-[4/3] overflow-hidden bg-sepia">
            <img src="${current.image}" alt="${current.title}" class="h-full w-full object-cover" loading="lazy" />
          </div>
          <p class="text-sm text-gray-600 leading-7 drop-cap">
            ${current.description}
          </p>
        </div>
      `
      : '';
  };

  const step = (direction) => {
    const total = stories.length || 1;
    currentIndex = (currentIndex + direction + total) % total;
    render();
  };

  const resetTimer = () => {
    if (rotationTimer) {
      window.clearInterval(rotationTimer);
    }
    rotationTimer = window.setInterval(() => step(1), 6000);
  };

  render();
  resetTimer();
  try {
    const data = await apiFetch('/api/stories');
    if (data?.items?.length) {
      stories = data.items.slice(0, 4);
      currentIndex = 0;
      render();
      resetTimer();
    }
  } catch (error) {
    // ignore
  }

  if (prevButton) {
    prevButton.addEventListener('click', () => {
      step(-1);
      resetTimer();
    });
  }
  if (nextButton) {
    nextButton.addEventListener('click', () => {
      step(1);
      resetTimer();
    });
  }

  let pointerStartX = 0;
  let pointerStartY = 0;
  let pointerActive = false;

  const onPointerStart = (event) => {
    const point = event.touches ? event.touches[0] : event;
    if (!point) {
      return;
    }
    pointerActive = true;
    pointerStartX = point.clientX;
    pointerStartY = point.clientY;
  };

  const onPointerEnd = (event) => {
    if (!pointerActive) {
      return;
    }
    const point = event.changedTouches ? event.changedTouches[0] : event;
    if (!point) {
      pointerActive = false;
      return;
    }
    const deltaX = point.clientX - pointerStartX;
    const deltaY = point.clientY - pointerStartY;
    pointerActive = false;
    if (Math.abs(deltaX) < 50 || Math.abs(deltaX) < Math.abs(deltaY)) {
      return;
    }
    if (deltaX > 0) {
      step(-1);
    } else {
      step(1);
    }
    resetTimer();
  };

  container.addEventListener('touchstart', onPointerStart, { passive: true });
  container.addEventListener('touchend', onPointerEnd, { passive: true });
  container.addEventListener('mousedown', onPointerStart);
  container.addEventListener('mouseup', onPointerEnd);
}

async function initProfileSetupPage() {
  const form = document.getElementById('profile-form');
  if (!form) {
    return;
  }
  const skillsInput = document.getElementById('profile-skills');
  const requiredSkillsInput = document.getElementById('profile-required-skills');
  const linksInput = document.getElementById('profile-links');
  const bioInput = document.getElementById('profile-bio');
  const availabilityInput = document.getElementById('profile-availability');
  const status = document.getElementById('profile-status');

  try {
    const data = await apiFetch('/api/profiles/me');
    if (skillsInput && data.skills) {
      skillsInput.value = data.skills.join(', ');
    }
    if (requiredSkillsInput && data.required_skills) {
      requiredSkillsInput.value = data.required_skills.join(', ');
    }
    if (linksInput && data.links) {
      linksInput.value = data.links.join(', ');
    }
    if (bioInput) {
      bioInput.value = data.bio || '';
    }
    if (availabilityInput) {
      availabilityInput.value = data.availability || '';
    }
    if (data.looking_for) {
      const radio = form.querySelector(`input[name="looking_for"][value="${data.looking_for}"]`);
      if (radio) {
        radio.checked = true;
      }
    }
  } catch (error) {
    if (status) {
      status.textContent = '';
    }
  }


  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const selected = form.querySelector('input[name="looking_for"]:checked');
    const lookingFor = selected ? selected.value : 'TEAM';
    const skills = skillsInput?.value
      ? skillsInput.value.split(',').map((skill) => skill.trim()).filter(Boolean)
      : [];
    const requiredSkills = requiredSkillsInput?.value
      ? requiredSkillsInput.value.split(',').map((skill) => skill.trim()).filter(Boolean)
      : [];
    if (!skills.length || !requiredSkills.length) {
      if (status) {
        status.textContent = 'Please add at least one skill and one skill you need.';
      }
      if (!skills.length && skillsInput) {
        skillsInput.focus();
      } else if (!requiredSkills.length && requiredSkillsInput) {
        requiredSkillsInput.focus();
      }
      return;
    }
    const links = linksInput?.value
      ? linksInput.value.split(',').map((link) => link.trim()).filter(Boolean)
      : [];
    const bioValue = bioInput?.value?.trim() || '';
    const availabilityValue = availabilityInput?.value?.trim() || '';
    if (!links.length) {
      if (status) {
        status.textContent = 'Please add at least one link.';
      }
      if (linksInput) {
        linksInput.focus();
      }
      return;
    }
    if (!bioValue) {
      if (status) {
        status.textContent = 'Please add a short bio.';
      }
      if (bioInput) {
        bioInput.focus();
      }
      return;
    }
    if (!availabilityValue) {
      if (status) {
        status.textContent = 'Please share your availability.';
      }
      if (availabilityInput) {
        availabilityInput.focus();
      }
      return;
    }
    const payload = {
      skills,
      required_skills: requiredSkills,
      links,
      looking_for: lookingFor,
      bio: bioValue,
      availability: availabilityValue,
    };
  if (status) {
    status.textContent = 'Saving profile...';
  }
  try {
    await apiFetch('/api/profiles/me', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (status) {
      status.textContent = 'Profile saved.';
    }
    window.setTimeout(() => {
      window.location.href = '/dashboard';
    }, 600);
  } catch (error) {
    if (status) {
      status.textContent = error.message || 'Unable to save profile.';
    }
  }
});
}

async function initAuthPage() {
  const button = document.getElementById('google-button');
  const devButton = document.getElementById('dev-login-button');
  if (!button) {
    return;
  }
  if (!window.google?.accounts?.id) {
    window.setTimeout(initAuthPage, 300);
    return;
  }

  const status = document.getElementById('auth-status');
  let config;
  try {
    config = await apiFetch('/api/config', { method: 'GET' });
  } catch (error) {
    if (status) {
      status.textContent = error.message;
    }
    return;
  }

  if (!config.google_client_id) {
    if (status) {
      status.textContent = 'Google client id missing. Update NYA_GOOGLE_CLIENT_ID in .env.';
    }
    return;
  }

  window.google.accounts.id.initialize({
    client_id: config.google_client_id,
    ux_mode: 'popup',
    auto_select: false,
    context: 'signin',
    callback: async (credentialResponse) => {
      if (!credentialResponse?.credential) {
        return;
      }
      if (status) {
        status.textContent = 'Signing in...';
      }
      try {
        await apiFetch('/api/auth/google/login', {
          method: 'POST',
          body: JSON.stringify({ id_token: credentialResponse.credential }),
        });
        await redirectAfterLogin();
      } catch (error) {
        if (status) {
          status.textContent = error.message;
        }
      }
    },
    use_fedcm_for_prompt: false,  
  });

  const containerWidth = button.getBoundingClientRect().width || button.parentElement?.getBoundingClientRect().width || 320;
  const targetWidth = 240;
  const buttonWidth = Math.min(Math.max(200, targetWidth), Math.floor(containerWidth));
  window.google.accounts.id.renderButton(button, {
    theme: 'outline',
    size: 'large',
    width: buttonWidth,
  });

  window.google.accounts.id.prompt((notification) => {
    if (notification.isNotDisplayed && notification.isNotDisplayed()) {
      const reason = notification.getNotDisplayedReason ? notification.getNotDisplayedReason() : 'unavailable';
      if (status) {
        status.textContent = `Google sign-in unavailable: ${reason}`;
      }
      return;
    }
    if (notification.isSkippedMoment && notification.isSkippedMoment()) {
      const reason = notification.getSkippedReason ? notification.getSkippedReason() : 'skipped';
      if (status) {
        status.textContent = `Google sign-in skipped: ${reason}`;
      }
    }
  });

  if (devButton) {
    devButton.addEventListener('click', async () => {
      const email = window.prompt('Enter a @thapar.edu email for dev login:');
      if (!email) {
        return;
      }
      const name = window.prompt('Display name (optional):') || undefined;
      if (status) {
        status.textContent = 'Signing in (dev)...';
      }
      try {
        await apiFetch('/api/auth/dev-login', {
          method: 'POST',
          body: JSON.stringify({ email, name }),
        });
        await redirectAfterLogin();
      } catch (error) {
        if (status) {
          status.textContent = error.message;
        }
      }
    });
  }
}

async function redirectAfterLogin() {
  let target = '/dashboard';
  try {
    const status = await apiFetch('/api/onboarding/status');
    if (!status.role_selected) {
      target = '/onboarding/role';
    } else if (status.role === 'MENTOR') {
      if (!status.has_profile) {
        target = '/mentor/setup';
      } else {
        target = status.mentor_approved ? '/mentor/dashboard' : '/mentor/pending';
      }
    } else {
      target = status.has_profile ? '/dashboard' : '/profile/setup';
    }
  } catch (error) {
    target = '/dashboard';
  }
  window.location.href = `/transition?target=${encodeURIComponent(target)}`;
}

function renderDiscoverList(items) {
  const container = document.getElementById('discover-list');
  if (!container) {
    return;
  }
  if (!items.length) {
    container.innerHTML = `
      <div class="col-span-full border border-warm-gray bg-white p-10 text-center">
        <p class="text-sm uppercase tracking-[0.2em] text-gray-400">No matches yet</p>
        <p class="text-xl font-serif text-primary mt-3">Try a skill keyword like "AI" or "Design".</p>
      </div>
    `;
    return;
  }
  const statusStyles = (status) => {
    switch (status) {
      case 'BOOKED':
        return 'text-red-600 border-red-200';
      case 'IN_TEAM':
        return 'text-gray-400 border-warm-gray';
      default:
        return 'text-green-600 border-green-200';
    }
  };
  const statusLabel = (status, count) => {
    switch (status) {
      case 'BOOKED':
        return `Booked · ${count}/5`;
      case 'IN_TEAM':
        return `In Team · ${count}/5`;
      default:
        return 'Available';
    }
  };
  container.innerHTML = items
    .map(
      (item) => `
      <div class="group discover-card relative flex flex-col gap-6 bg-white border border-warm-gray hover:shadow-xl hover:shadow-gray-100 transition-all duration-500 cursor-pointer p-8" data-user-id="${item.id}">
        <span class="absolute top-6 right-6 text-[10px] font-bold tracking-widest uppercase ${statusStyles(item.team_status)} border px-2 py-1">
          ${statusLabel(item.team_status, item.team_count)}
        </span>
        <div class="discover-media w-20 h-20 bg-warm-gray border border-warm-gray p-1">
          <div class="w-full h-full bg-cover bg-center" style="background-image: url('${getAvatarUrl(item.id)}')"></div>
        </div>
        <div class="discover-body">
          <div class="mb-6">
            <div>
              <h3 class="text-2xl text-primary mb-1">${item.name}</h3>
              <p class="text-[11px] font-bold uppercase tracking-[0.15em] text-gray-400">${item.looking_for}</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2 pt-6 border-t border-warm-gray">
            ${item.skills.map((skill) => `<span class="text-[10px] uppercase tracking-tighter text-gray-500">${skill}</span>`).join('')}
          </div>
        </div>
      </div>
      `
    )
    .join('');

  container.querySelectorAll('[data-user-id]').forEach((node) => {
    node.addEventListener('click', () => {
      const userId = node.getAttribute('data-user-id');
      window.location.href = `/profile?user_id=${userId}`;
    });
  });
}

function renderRecommended(items) {
  const container = document.getElementById('recommended-list');
  if (!container) {
    return;
  }
  if (!items.length) {
    container.innerHTML = `
      <div class="border border-warm-gray bg-white/70 p-6 text-center">
        <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No curated matches</p>
        <p class="text-sm text-gray-500 mt-2">Update your skills to improve recommendations.</p>
      </div>
    `;
    return;
  }
  const statusStyles = (status) => {
    switch (status) {
      case 'BOOKED':
        return 'text-red-600 border-red-200';
      case 'IN_TEAM':
        return 'text-gray-400 border-warm-gray';
      default:
        return 'text-green-600 border-green-200';
    }
  };
  const statusLabel = (status, count) => {
    switch (status) {
      case 'BOOKED':
        return `Booked · ${count}/5`;
      case 'IN_TEAM':
        return `In Team · ${count}/5`;
      default:
        return 'Available';
    }
  };
  container.innerHTML = items
    .map(
      (item) => `
      <div class="group cursor-pointer" data-user-id="${item.id}">
        <div class="flex items-center gap-5 mb-3">
          <div class="w-14 h-14 bg-white border border-warm-gray p-0.5">
            <div class="w-full h-full bg-cover bg-center" style="background-image: url('${getAvatarUrl(item.id)}')"></div>
          </div>
          <div>
            <p class="text-lg font-serif text-primary group-hover:underline">${item.name}</p>
            <p class="text-[10px] font-bold uppercase tracking-widest text-gray-400">${item.skills[0] || 'Capstone'}</p>
          </div>
        </div>
        <div class="flex justify-between items-center text-[11px] border-t border-warm-gray pt-2 mt-2">
          <span class="font-medium text-gray-500">${statusLabel(item.team_status, item.team_count)}</span>
          <span class="text-[9px] font-semibold uppercase tracking-[0.2em] ${statusStyles(item.team_status)} border px-2 py-0.5">${statusLabel(item.team_status, item.team_count)}</span>
          <span class="material-symbols-outlined text-gray-300 scale-75">arrow_forward_ios</span>
        </div>
      </div>
      `
    )
    .join('');

  container.querySelectorAll('[data-user-id]').forEach((node) => {
    node.addEventListener('click', () => {
      const userId = node.getAttribute('data-user-id');
      window.location.href = `/profile?user_id=${userId}`;
    });
  });
}

async function initDashboardPage() {
  const discoverInput = document.getElementById('discover-search');
  const countLabel = document.getElementById('discover-count');
  const logoutButton = document.getElementById('logout-button');
  const viewMatches = document.getElementById('view-matches');
  const scrollContainer = document.getElementById('dashboard-scroll');
  const discoverSection = document.getElementById('discover-section');
  const discoverList = document.getElementById('discover-list');
  const viewGrid = document.getElementById('view-grid');
  const viewList = document.getElementById('view-list');
  const prevButton = document.getElementById('discover-prev');
  const nextButton = document.getElementById('discover-next');
  const pageLabel = document.getElementById('discover-page');
  const profileLink = document.getElementById('nav-profile-link');
  const shuffleButton = document.getElementById('shuffle-match');
  const shuffleModal = document.getElementById('shuffle-modal');
  const shuffleClose = document.getElementById('shuffle-close');
  const shuffleCard = document.getElementById('shuffle-card');
  const shuffleNext = document.getElementById('shuffle-next');
  const shuffleRequest = document.getElementById('shuffle-request');
  let shuffleItems = [];
  let shuffleIndex = 0;
  let currentPage = 1;
  const pageSize = 12;
  if (!discoverInput && !document.getElementById('discover-list')) {
    return;
  }

  async function loadDiscover() {
    const term = discoverInput?.value?.trim();
    const params = new URLSearchParams();
    if (term) {
      params.set('search', term);
    }
    params.set('page', String(currentPage));
    params.set('limit', String(pageSize));
    const query = params.toString() ? `?${params.toString()}` : '';
    const data = await apiFetch(`/api/users/discover${query}`);
    renderDiscoverList(data);
    if (countLabel) {
      countLabel.textContent = `Showing ${data.length} Candidates`;
    }
    if (pageLabel) {
      pageLabel.textContent = `Page ${currentPage}`;
    }
    if (prevButton) {
      prevButton.disabled = currentPage <= 1;
      prevButton.classList.toggle('opacity-50', prevButton.disabled);
      prevButton.classList.toggle('cursor-not-allowed', prevButton.disabled);
    }
    if (nextButton) {
      const hasNext = data.length === pageSize;
      nextButton.disabled = !hasNext;
      nextButton.classList.toggle('opacity-50', nextButton.disabled);
      nextButton.classList.toggle('cursor-not-allowed', nextButton.disabled);
    }
  }

  async function loadRecommended() {
    const data = await apiFetch('/api/users/recommended');
    renderRecommended(data);
  }

  const setViewMode = (mode) => {
    if (!discoverList || !viewGrid || !viewList) {
      return;
    }
    const isList = mode === 'list';
    discoverList.classList.toggle('list-view', isList);
    ['grid', 'md:grid-cols-2', 'lg:grid-cols-3', 'gap-10'].forEach((cls) => {
      discoverList.classList.toggle(cls, !isList);
    });
    ['flex', 'flex-col', 'gap-4'].forEach((cls) => {
      discoverList.classList.toggle(cls, isList);
    });
    viewGrid.classList.toggle('text-primary', !isList);
    viewGrid.classList.toggle('text-gray-300', isList);
    viewGrid.classList.toggle('hover:text-primary', isList);
    viewGrid.setAttribute('aria-pressed', String(!isList));
    viewList.classList.toggle('text-primary', isList);
    viewList.classList.toggle('text-gray-300', !isList);
    viewList.classList.toggle('hover:text-primary', !isList);
    viewList.setAttribute('aria-pressed', String(isList));
  };

  if (viewGrid && viewList) {
    viewGrid.addEventListener('click', () => setViewMode('grid'));
    viewList.addEventListener('click', () => setViewMode('list'));
  }

  const renderShuffleCard = () => {
    if (!shuffleCard) {
      return;
    }
    if (!shuffleItems.length) {
      shuffleCard.innerHTML = `
        <div class="text-center py-12">
          <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No matches</p>
          <p class="text-lg font-serif text-primary mt-3">Try a search or refresh later.</p>
        </div>
      `;
      return;
    }
    const item = shuffleItems[shuffleIndex % shuffleItems.length];
    const statusLabel = item.team_status === 'BOOKED'
      ? `Booked · ${item.team_count}/5`
      : item.team_status === 'IN_TEAM'
        ? `In Team · ${item.team_count}/5`
        : 'Available';
    const statusStyles = item.team_status === 'BOOKED'
      ? 'text-red-600 border-red-200'
      : item.team_status === 'IN_TEAM'
        ? 'text-gray-400 border-warm-gray'
        : 'text-green-600 border-green-200';
    shuffleCard.classList.remove('enter');
    shuffleCard.innerHTML = `
      <div class="flex flex-col md:flex-row gap-8">
        <div class="w-full md:w-44 h-56 bg-warm-gray border border-warm-gray p-2">
          <div class="w-full h-full bg-cover bg-center" style="background-image: url('${getAvatarUrl(item.id)}')"></div>
        </div>
        <div class="flex-1">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h4 class="text-3xl text-primary">${item.name}</h4>
              <p class="text-[11px] font-bold uppercase tracking-[0.2em] text-gray-400 mt-2">Looking for: ${item.looking_for}</p>
            </div>
            <span class="text-[10px] font-bold tracking-widest uppercase ${statusStyles} border px-2 py-1">${statusLabel}</span>
          </div>
          <p class="text-sm text-gray-500 mt-6">Skills</p>
          <div class="flex flex-wrap gap-2 mt-3">
            ${(item.skills || []).map((skill) => `<span class="text-[10px] uppercase tracking-tighter text-gray-500">${skill}</span>`).join('')}
          </div>
        </div>
      </div>
    `;
    requestAnimationFrame(() => {
      shuffleCard.classList.add('enter');
    });
  };

  const openShuffle = async () => {
    if (!shuffleModal) {
      return;
    }
    shuffleModal.classList.remove('hidden');
    shuffleModal.classList.add('flex');
    try {
      const data = await apiFetch('/api/users/discover?limit=30&page=1');
      shuffleItems = data.sort(() => Math.random() - 0.5);
      shuffleIndex = 0;
      renderShuffleCard();
    } catch (error) {
      shuffleItems = [];
      renderShuffleCard();
    }
  };

  if (shuffleButton) {
    shuffleButton.addEventListener('click', openShuffle);
  }
  if (shuffleClose) {
    shuffleClose.addEventListener('click', () => {
      shuffleModal.classList.add('hidden');
      shuffleModal.classList.remove('flex');
    });
  }
  if (shuffleNext) {
    shuffleNext.addEventListener('click', () => {
      if (!shuffleItems.length) {
        return;
      }
      shuffleIndex = (shuffleIndex + 1) % shuffleItems.length;
      renderShuffleCard();
    });
  }
  if (shuffleRequest) {
    shuffleRequest.addEventListener('click', () => {
      if (!shuffleItems.length) {
        return;
      }
      const item = shuffleItems[shuffleIndex % shuffleItems.length];
      window.location.href = `/requests/new?user_id=${item.id}`;
    });
  }

  if (discoverInput) {
    discoverInput.addEventListener('input', () => {
      window.clearTimeout(discoverInput._timer);
      discoverInput._timer = window.setTimeout(() => {
        currentPage = 1;
        loadDiscover();
      }, 400);
    });
  }
  if (prevButton) {
    prevButton.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage -= 1;
        loadDiscover();
      }
    });
  }
  if (nextButton) {
    nextButton.addEventListener('click', () => {
      currentPage += 1;
      loadDiscover();
    });
  }

  await Promise.all([
    loadDiscover(),
    loadRecommended(),
  ]);
  if (logoutButton) {
    logoutButton.addEventListener('click', async () => {
      try {
        await apiFetch('/api/auth/logout', { method: 'POST' });
      } finally {
        window.location.href = '/authentication';
      }
    });
  }

  if (viewMatches && scrollContainer && discoverSection) {
    viewMatches.addEventListener('click', () => {
      const offset = discoverSection.getBoundingClientRect().top - scrollContainer.getBoundingClientRect().top;
      const target = scrollContainer.scrollTop + offset - 24;
      if (scrollContainer.scrollHeight > scrollContainer.clientHeight + 8) {
        scrollContainer.scrollTo({
          top: target,
          behavior: 'smooth',
        });
      } else {
        discoverSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  setViewMode('grid');
}

async function initProfilePage() {
  const profileId = getQueryParam('user_id');
  const requestButton = document.getElementById('request-access');
  if (!profileId) {
    return;
  }

  const profile = await apiFetch(`/api/profiles/${profileId}`);
  setText('profile-name', profile.name);
  setText('profile-role', profile.role);
  setText('profile-looking', profile.looking_for === 'TEAM' ? 'Looking for Team' : 'Looking for Member');
  setText('profile-bio', profile.bio || '');
  setText('profile-availability', profile.availability || '');

  const skills = document.getElementById('profile-skills');
  if (skills) {
    skills.innerHTML = createSkillChips(profile.skills || []);
  }

  if (requestButton) {
    requestButton.addEventListener('click', async () => {
      window.location.href = `/requests/new?user_id=${profile.user_id}`;
    });
  }
}

async function initRequestMessagePage() {
  const form = document.getElementById('request-message-form');
  if (!form) {
    return;
  }
  const nameEl = document.getElementById('request-message-name');
  const roleEl = document.getElementById('request-message-role');
  const messageEl = document.getElementById('request-message');
  const statusEl = document.getElementById('request-message-status');
  const backLink = document.getElementById('request-message-back');
  const profileId = getQueryParam('user_id');
  if (!profileId) {
    if (statusEl) {
      statusEl.textContent = 'Missing user information.';
    }
    return;
  }

  if (backLink) {
    backLink.href = `/profile?user_id=${profileId}`;
  }

  try {
    const profile = await apiFetch(`/api/profiles/${profileId}`);
    if (nameEl) nameEl.textContent = profile.name || 'Member';
    if (roleEl) roleEl.textContent = profile.role || '';
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = error.message || 'Unable to load profile.';
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = messageEl?.value?.trim();
    if (!message) {
      if (statusEl) {
        statusEl.textContent = 'Please add a short message.';
      }
      return;
    }
    if (statusEl) {
      statusEl.textContent = 'Sending request...';
    }
    try {
      await apiFetch('/api/requests', {
        method: 'POST',
        body: JSON.stringify({ to_user_id: profileId, type: 'CAPSTONE', message }),
      });
      if (statusEl) {
        statusEl.textContent = 'Request sent. Redirecting...';
      }
      window.setTimeout(() => {
        window.location.href = '/requests';
      }, 700);
    } catch (error) {
      if (statusEl) {
        statusEl.textContent = error.message || 'Unable to send request.';
      }
    }
  });
}

function renderPrefectList(mentors) {
  const container = document.getElementById('mentor-list');
  if (!container) {
    return;
  }
  container.innerHTML = mentors
    .map(
      (mentor) => `
      <div class="fellowship-row group flex flex-col md:flex-row md:items-center py-12 transition-all" data-mentor-id="${mentor.user_id}">
        <div class="flex-1">
          <div class="flex items-center gap-4 mb-2">
            <span class="text-[10px] font-bold text-accent-gold uppercase tracking-[0.2em]">${mentor.domain}</span>
            <span class="h-px w-8 bg-accent-gold/30"></span>
            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">${mentor.experience_years}+ Years Experience</span>
          </div>
          <h3 class="mentor-name text-4xl font-serif text-primary dark:text-white mb-2 transition-colors">${mentor.name}</h3>
          <p class="text-sm font-light text-gray-500">${mentor.bio || ''}</p>
        </div>
        <div class="flex-1 mt-6 md:mt-0">
          <span class="text-[10px] font-bold text-primary/40 dark:text-white/40 uppercase tracking-widest block mb-2">Expertise</span>
          <p class="text-lg font-serif text-primary/80 dark:text-gray-300 leading-relaxed">${(mentor.expertise || []).join(', ')}</p>
        </div>
        <div class="flex items-center justify-end md:ml-12 mt-8 md:mt-0">
          <a class="group relative inline-flex items-center justify-center px-10 py-3 overflow-hidden font-bold transition-all bg-primary dark:bg-white text-white dark:text-primary hover:bg-navy-deep dark:hover:bg-gray-200" href="/mentors/request?mentor_id=${mentor.id}">
            <span class="text-[10px] uppercase tracking-[0.25em]">Request Prefect</span>
          </a>
        </div>
      </div>
      `
    )
    .join('');
}

async function initPrefectRequestPage() {
  const form = document.getElementById('mentor-request-form');
  if (!form) {
    return;
  }
  const nameEl = document.getElementById('mentor-request-name');
  const domainEl = document.getElementById('mentor-request-domain');
  const bioEl = document.getElementById('mentor-request-bio');
  const messageEl = document.getElementById('mentor-request-message');
  const statusEl = document.getElementById('mentor-request-status');

  const mentorId = getQueryParam('mentor_id');
  if (!mentorId) {
    if (statusEl) {
      statusEl.textContent = 'Missing mentor information.';
    }
    return;
  }

  let targetUserId = null;
  try {
    const mentor = await apiFetch(`/api/mentors/${mentorId}`);
    targetUserId = mentor.user_id;
    if (nameEl) nameEl.textContent = mentor.name || 'Prefect';
    if (domainEl) domainEl.textContent = mentor.domain || '';
    if (bioEl) bioEl.textContent = mentor.bio || '';
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = error.message || 'Unable to load mentor.';
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = messageEl?.value?.trim();
    if (!message) {
      if (statusEl) {
        statusEl.textContent = 'Please add a short message.';
      }
      return;
    }
    if (statusEl) {
      statusEl.textContent = 'Submitting request...';
    }
    try {
      if (!targetUserId) {
        if (statusEl) {
          statusEl.textContent = 'Mentor profile not available.';
        }
        return;
      }
      await apiFetch('/api/requests', {
        method: 'POST',
        body: JSON.stringify({ to_user_id: targetUserId, type: 'MENTORSHIP', message }),
      });
      if (statusEl) {
        statusEl.textContent = 'Request sent. Redirecting...';
      }
      window.setTimeout(() => {
        window.location.href = '/requests';
      }, 1000);
    } catch (error) {
      if (statusEl) {
        statusEl.textContent = error.message || 'Unable to send request.';
      }
    }
  });
}

async function initPrefectsPage() {
  const input = document.getElementById('mentor-search');
  const countLabel = document.getElementById('mentor-count');
  if (!input && !document.getElementById('mentor-list')) {
    return;
  }

  async function loadPrefects() {
    const term = input?.value?.trim();
    const query = term ? `?search=${encodeURIComponent(term)}` : '';
    const data = await apiFetch(`/api/mentors${query}`);
    renderPrefectList(data);
    if (countLabel) {
      countLabel.textContent = `${data.length} mentors available`;
    }
  }

  if (input) {
    input.addEventListener('input', () => {
      window.clearTimeout(input._timer);
      input._timer = window.setTimeout(loadPrefects, 400);
    });
  }

  await loadPrefects();

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN') {
      const adminLink = document.getElementById('admin-nav');
      if (adminLink) {
        adminLink.classList.remove('hidden');
      }
    }
    if (status.role === 'MENTOR' && status.mentor_approved) {
      const mentorLink = document.getElementById('mentor-nav');
      if (mentorLink) {
        mentorLink.classList.remove('hidden');
      }
    }
  } catch (error) {
    // ignore
  }
}

function renderRequestRow(request, incoming) {
  return `
  <div class="flex items-center justify-between px-8 py-7 border-b border-border-sep/60 last:border-0 hover:bg-white/40 transition-colors" data-request-id="${request.id}">
    <div class="flex items-center gap-6">
      <div class="flex flex-col">
        <p class="text-[16px] text-charcoal font-medium leading-snug">${incoming ? request.counterpart_name + ' sent a request' : 'Request to ' + request.counterpart_name}</p>
        <div class="flex items-center gap-2 mt-1">
          <span class="text-xs uppercase tracking-wider text-charcoal/40 font-bold">${request.type}</span>
          <span class="text-[13px] text-charcoal/60">${request.status}</span>
        </div>
        ${request.counterpart_email ? `<div class="text-[12px] text-charcoal/70 mt-2">Email: ${request.counterpart_email}</div>` : ''}
      </div>
    </div>
    ${incoming ? `
    <div class="flex gap-6 items-center">
      <button class="text-xs uppercase tracking-[0.15em] font-bold text-navy-academic hover:underline decoration-navy-academic/30 underline-offset-4" data-action="accept">
        Accept
      </button>
      <button class="text-xs uppercase tracking-[0.15em] font-bold text-charcoal/40 hover:text-charcoal transition-colors" data-action="reject">
        Decline
      </button>
    </div>
    ` : ''}
  </div>
  `;
}

function renderTeamRow(request) {
  return `
  <div class="flex items-center justify-between px-8 py-7 border-b border-border-sep/60 last:border-0 hover:bg-white/40 transition-colors">
    <div class="flex items-center gap-6">
      <div class="flex flex-col">
        <p class="text-[16px] text-charcoal font-medium leading-snug">${request.counterpart_name}</p>
        <div class="flex items-center gap-2 mt-1">
          <span class="text-xs uppercase tracking-wider text-charcoal/40 font-bold">${request.type}</span>
          <span class="text-[13px] text-charcoal/60">Accepted</span>
        </div>
        ${request.counterpart_email ? `<div class="text-[12px] text-charcoal/70 mt-2">Email: ${request.counterpart_email}</div>` : ''}
      </div>
    </div>
  </div>
  `;
}

function initLogoutButtons() {
  const buttons = document.querySelectorAll('#logout-button, [data-logout]');
  if (!buttons.length) {
    return;
  }
  buttons.forEach((button) => {
    button.addEventListener('click', async () => {
      try {
        await apiFetch('/api/auth/logout', { method: 'POST' });
      } finally {
        window.location.href = '/authentication';
      }
    });
  });
}

function initMobileNav() {
  const headers = document.querySelectorAll('header');
  if (!headers.length) {
    return;
  }

  headers.forEach((header, index) => {
    const nav = header.querySelector('nav');
    if (!nav || header.querySelector('[data-mobile-nav-toggle]')) {
      return;
    }
    const rightSlot = header.querySelector('.flex.items-center.gap-6');
    if (!rightSlot) {
      return;
    }

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className =
      'md:hidden inline-flex items-center justify-center w-10 h-10 border border-warm-gray text-primary';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', `mobile-nav-panel-${index}`);
    toggle.setAttribute('data-mobile-nav-toggle', '');
    toggle.innerHTML = '<span class="material-symbols-outlined">menu</span>';
    rightSlot.insertBefore(toggle, rightSlot.firstChild);

    const panel = document.createElement('div');
    panel.className = 'mobile-nav-panel md:hidden hidden';
    panel.id = `mobile-nav-panel-${index}`;
    panel.setAttribute('data-mobile-nav-panel', '');

    const links = Array.from(nav.querySelectorAll('a'));
    panel.innerHTML = links
      .map((link) => {
        const text = link.textContent?.trim() || '';
        const href = link.getAttribute('href') || '#';
        const hidden = link.classList.contains('hidden') ? ' hidden' : '';
        const dataNav = link.id ? ` data-nav-id="${link.id}"` : '';
        return `<a class="mobile-nav-link${hidden}"${dataNav} href="${href}">${text}</a>`;
      })
      .join('');

    if (header.querySelector('#logout-button')) {
      panel.innerHTML += '<button class="mobile-nav-action" data-logout type="button">Logout</button>';
    }

    header.after(panel);

    const closePanel = () => {
      panel.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
    };
    const openPanel = () => {
      panel.classList.remove('hidden');
      toggle.setAttribute('aria-expanded', 'true');
    };

    toggle.addEventListener('click', () => {
      if (panel.classList.contains('hidden')) {
        openPanel();
      } else {
        closePanel();
      }
    });

    panel.querySelectorAll('a, [data-logout]').forEach((node) => {
      node.addEventListener('click', () => {
        closePanel();
      });
    });
  });
}

async function initRequestsPage() {
  const incomingContainer = document.getElementById('incoming-requests');
  const outgoingContainer = document.getElementById('outgoing-requests');
  const teamContainer = document.getElementById('team-members');
  const teamCount = document.getElementById('team-count');
  const acceptedContainer = document.getElementById('accepted-requests');
  const archivedContainer = document.getElementById('archived-requests');
  const tabPending = document.getElementById('requests-tab-pending');
  const tabAccepted = document.getElementById('requests-tab-accepted');
  const tabArchived = document.getElementById('requests-tab-archived');
  const sectionPending = document.getElementById('requests-pending');
  const sectionAccepted = document.getElementById('requests-accepted');
  const sectionArchived = document.getElementById('requests-archived');
  if (!incomingContainer && !outgoingContainer && !teamContainer) {
    return;
  }

  const [incoming, outgoing] = await Promise.all([
    apiFetch('/api/requests/incoming'),
    apiFetch('/api/requests/outgoing'),
  ]);

  if (incomingContainer) {
    const pendingIncoming = incoming.filter((request) => request.status === 'PENDING');
    incomingContainer.innerHTML = pendingIncoming.map((request) => renderRequestRow(request, true)).join('');
    incomingContainer.querySelectorAll('[data-action="accept"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const row = event.currentTarget.closest('[data-request-id]');
        const id = row?.getAttribute('data-request-id');
        if (!id) {
          return;
        }
        await apiFetch(`/api/requests/${id}/accept`, { method: 'POST' });
        await initRequestsPage();
      });
    });
    incomingContainer.querySelectorAll('[data-action="reject"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const row = event.currentTarget.closest('[data-request-id]');
        const id = row?.getAttribute('data-request-id');
        if (!id) {
          return;
        }
        await apiFetch(`/api/requests/${id}/reject`, { method: 'POST' });
        await initRequestsPage();
      });
    });
  }

  if (outgoingContainer) {
    const pendingOutgoing = outgoing.filter((request) => request.status === 'PENDING');
    outgoingContainer.innerHTML = pendingOutgoing.map((request) => renderRequestRow(request, false)).join('');
  }

  if (acceptedContainer) {
    const accepted = [
      ...incoming.filter((request) => request.status === 'ACCEPTED').map((request) => ({ request, incoming: true })),
      ...outgoing.filter((request) => request.status === 'ACCEPTED').map((request) => ({ request, incoming: false })),
    ];
    acceptedContainer.innerHTML = accepted.length
      ? accepted.map(({ request, incoming }) => renderRequestRow(request, incoming)).join('')
      : `
        <div class="px-8 py-7 text-sm text-charcoal/60">
          No accepted requests yet.
        </div>
      `;
  }

  if (archivedContainer) {
    const archived = [
      ...incoming.filter((request) => request.status === 'REJECTED').map((request) => ({ request, incoming: true })),
      ...outgoing.filter((request) => request.status === 'REJECTED').map((request) => ({ request, incoming: false })),
    ];
    archivedContainer.innerHTML = archived.length
      ? archived.map(({ request, incoming }) => renderRequestRow(request, incoming)).join('')
      : `
        <div class="px-8 py-7 text-sm text-charcoal/60">
          No archived requests yet.
        </div>
      `;
  }

  if (teamContainer) {
    const accepted = [...incoming, ...outgoing].filter((request) => request.status === 'ACCEPTED');
    if (teamCount) {
      teamCount.textContent = `${accepted.length} members`;
    }
    teamContainer.innerHTML = accepted.length
      ? accepted.map((request) => renderTeamRow(request)).join('')
      : `
        <div class="px-8 py-7 text-sm text-charcoal/60">
          No accepted members yet.
        </div>
      `;
  }

  const setTab = (tab) => {
    if (!sectionPending || !sectionAccepted || !sectionArchived) {
      return;
    }
    sectionPending.classList.toggle('hidden', tab !== 'pending');
    sectionAccepted.classList.toggle('hidden', tab !== 'accepted');
    sectionArchived.classList.toggle('hidden', tab !== 'archived');
    if (tabPending) {
      tabPending.classList.toggle('border-navy-academic', tab === 'pending');
      tabPending.classList.toggle('text-navy-academic', tab === 'pending');
      tabPending.classList.toggle('text-charcoal/40', tab !== 'pending');
    }
    if (tabAccepted) {
      tabAccepted.classList.toggle('border-navy-academic', tab === 'accepted');
      tabAccepted.classList.toggle('text-navy-academic', tab === 'accepted');
      tabAccepted.classList.toggle('text-charcoal/40', tab !== 'accepted');
    }
    if (tabArchived) {
      tabArchived.classList.toggle('border-navy-academic', tab === 'archived');
      tabArchived.classList.toggle('text-navy-academic', tab === 'archived');
      tabArchived.classList.toggle('text-charcoal/40', tab !== 'archived');
    }
  };

  if (tabPending) {
    tabPending.addEventListener('click', () => setTab('pending'));
  }
  if (tabAccepted) {
    tabAccepted.addEventListener('click', () => setTab('accepted'));
  }
  if (tabArchived) {
    tabArchived.addEventListener('click', () => setTab('archived'));
  }
  setTab('pending');

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN') {
      const adminLink = document.getElementById('admin-nav');
      if (adminLink) {
        adminLink.classList.remove('hidden');
      }
    }
    if (status.role === 'MENTOR' && status.mentor_approved) {
      const mentorLink = document.getElementById('mentor-nav');
      if (mentorLink) {
        mentorLink.classList.remove('hidden');
      }
    }
  } catch (error) {
    // ignore
  }
}

async function initRoleSelectionPage() {
  const userButton = document.getElementById('role-user');
  const mentorButton = document.getElementById('role-mentor');
  const status = document.getElementById('role-status');
  if (!userButton && !mentorButton) {
    return;
  }

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN') {
      const adminLink = document.getElementById('admin-nav');
      if (adminLink) {
        adminLink.classList.remove('hidden');
      }
    }
    if (status.role === 'MENTOR' && status.mentor_approved) {
      const mentorLink = document.getElementById('mentor-nav');
      if (mentorLink) {
        mentorLink.classList.remove('hidden');
      }
    }
  } catch (error) {
    // ignore
  }

  const setRole = async (role) => {
    if (status) {
      status.textContent = 'Saving your choice...';
    }
    try {
      await apiFetch('/api/onboarding/role', {
        method: 'POST',
        body: JSON.stringify({ role }),
      });
      window.location.href = role === 'MENTOR' ? '/mentor/setup' : '/profile/setup';
    } catch (error) {
      if (status) {
        status.textContent = error.message;
      }
    }
  };

  if (userButton) {
    userButton.addEventListener('click', () => setRole('USER'));
  }
  if (mentorButton) {
    mentorButton.addEventListener('click', () => setRole('MENTOR'));
  }
}

async function initPrefectSetupPage() {
  const form = document.getElementById('mentor-form');
  if (!form) {
    return;
  }

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role === 'ADMIN') {
      const adminLink = document.getElementById('admin-nav');
      if (adminLink) {
        adminLink.classList.remove('hidden');
      }
    }
    if (status.role === 'MENTOR' && status.mentor_approved) {
      const mentorLink = document.getElementById('mentor-nav');
      if (mentorLink) {
        mentorLink.classList.remove('hidden');
      }
    }
  } catch (error) {
    // ignore
  }
  const domainInput = document.getElementById('mentor-domain');
  const experienceInput = document.getElementById('mentor-experience');
  const expertiseInput = document.getElementById('mentor-expertise');
  const linksInput = document.getElementById('mentor-links');
  const bioInput = document.getElementById('mentor-bio');
  const availabilityInput = document.getElementById('mentor-availability');
  const status = document.getElementById('mentor-status');

  try {
    const data = await apiFetch('/api/mentors/me');
    if (domainInput) domainInput.value = data.domain || '';
    if (experienceInput) experienceInput.value = data.experience_years ?? '';
    if (expertiseInput && data.expertise) expertiseInput.value = data.expertise.join(', ');
    if (linksInput && data.links) linksInput.value = data.links.join(', ');
    if (bioInput) bioInput.value = data.bio || '';
    if (availabilityInput) availabilityInput.value = data.availability || '';
    if (status && data.approved_by_admin) {
      status.textContent = 'Approved. Redirecting to mentor dashboard...';
      window.setTimeout(() => {
        window.location.href = '/mentor/dashboard';
      }, 600);
    } else if (status) {
      status.textContent = 'Pending admin approval.';
    }
  } catch (error) {
    if (status) {
      status.textContent = '';
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      domain: domainInput?.value || '',
      experience_years: Number(experienceInput?.value || 0),
      expertise: expertiseInput?.value
        ? expertiseInput.value.split(',').map((skill) => skill.trim()).filter(Boolean)
        : [],
      links: linksInput?.value
        ? linksInput.value.split(',').map((link) => link.trim()).filter(Boolean)
        : [],
      bio: bioInput?.value || '',
      availability: availabilityInput?.value || '',
    };
    if (status) {
      status.textContent = 'Submitting for review...';
    }
    try {
      await apiFetch('/api/mentors/me', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (status) {
        status.textContent = 'Submitted. Awaiting admin approval.';
      }
      window.setTimeout(() => {
        window.location.href = '/mentor/pending';
      }, 500);
    } catch (error) {
      if (status) {
        status.textContent = error.message || 'Unable to submit.';
      }
    }
  });
}

async function initAdminPrefectsPage() {
  const container = document.getElementById('admin-mentor-list');
  const status = document.getElementById('admin-mentor-status');
  if (!container) {
    return;
  }

  try {
    const me = await apiFetch('/api/users/me');
    if (me.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
  } catch (error) {
    window.location.href = '/authentication';
    return;
  }

  const load = async () => {
    const data = await apiFetch('/api/admin/mentors/pending');
    if (!data.length) {
      container.innerHTML = `
        <div class="border border-warm-gray bg-white/70 p-6 text-center">
          <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No pending mentors</p>
          <p class="text-sm text-gray-500 mt-2">New mentor submissions will appear here.</p>
        </div>
      `;
      return;
    }
    container.innerHTML = data
      .map(
        (mentor) => `
        <div class="border border-warm-gray bg-white p-6" data-mentor-id="${mentor.id}">
          <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div>
              <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">${mentor.domain}</p>
              <h3 class="text-2xl text-primary mt-2">${mentor.name}</h3>
              <p class="text-sm text-gray-500 mt-2">${mentor.bio || ''}</p>
              <p class="text-xs text-gray-400 mt-2">Email: ${mentor.email}</p>
              <p class="text-xs text-gray-400 mt-1">Experience: ${mentor.experience_years} yrs</p>
              <p class="text-xs text-gray-400 mt-1">Expertise: ${(mentor.expertise || []).join(', ')}</p>
              <p class="text-xs text-gray-400 mt-1">Links: ${(mentor.links || []).join(', ')}</p>
            </div>
            <div class="flex gap-3">
              <button class="border border-primary text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="approve">Approve</button>
              <button class="border border-warm-gray text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="reject">Reject</button>
            </div>
          </div>
        </div>
        `
      )
      .join('');

    container.querySelectorAll('[data-action="approve"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-mentor-id]');
        const id = card?.getAttribute('data-mentor-id');
        if (!id) return;
        await apiFetch(`/api/admin/mentors/${id}/approve`, { method: 'POST' });
        await load();
      });
    });
    container.querySelectorAll('[data-action="reject"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-mentor-id]');
        const id = card?.getAttribute('data-mentor-id');
        if (!id) return;
        await apiFetch(`/api/admin/mentors/${id}/reject`, { method: 'POST' });
        await load();
      });
    });
  };

  try {
    await load();
  } catch (error) {
    if (status) {
      status.textContent = error.message;
    }
  }
}

async function initAdminUsersPage() {
  const container = document.getElementById('admin-user-list');
  const status = document.getElementById('admin-user-status');
  const search = document.getElementById('admin-user-search');
  const totalCount = document.getElementById('admin-user-count');
  if (!container) {
    return;
  }

  try {
    const me = await apiFetch('/api/users/me');
    if (me.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
  } catch (error) {
    window.location.href = '/authentication';
    return;
  }

  const render = (data) => {
    if (!data.length) {
      container.innerHTML = `
        <div class="border border-warm-gray bg-white/70 p-6 text-center">
          <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No users found</p>
        </div>
      `;
      return;
    }
    container.innerHTML = data
      .map(
        (user) => `
        <div class="border border-warm-gray bg-white p-6" data-user-id="${user.id}">
          <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div>
              <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">${user.role}</p>
              ${user.role !== 'ADMIN'
                ? `<a class="text-2xl text-primary mt-2 inline-block hover:opacity-80 transition-opacity" href="/profile?user_id=${user.id}">${user.name}</a>`
                : `<h3 class="text-2xl text-primary mt-2">${user.name}</h3>`}
              <p class="text-sm text-gray-500 mt-2">${user.email}</p>
              <p class="text-xs text-gray-400 mt-1">Created: ${new Date(user.created_at).toLocaleDateString()}</p>
              <p class="text-xs text-gray-400 mt-1">Last login: ${new Date(user.last_login).toLocaleDateString()}</p>
              <p class="text-xs text-gray-400 mt-1">Blocked: ${user.blocked ? 'Yes' : 'No'}</p>
            </div>
            <div class="flex gap-3 flex-wrap">
              ${user.role !== 'ADMIN'
                ? `<a class="border border-primary text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" href="/profile?user_id=${user.id}">View Profile</a>`
                : ''}
              ${user.role === 'ADMIN'
                ? '<button class="border border-primary text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="remove-admin">Remove Admin</button>'
                : '<button class="border border-primary text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="make-admin">Make Admin</button>'}
              ${user.blocked
                ? '<button class="border border-warm-gray text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="unblock">Unblock</button>'
                : '<button class="border border-warm-gray text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="block">Block</button>'}
              <button class="border border-warm-gray text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="reset-profile">Reset Profile</button>
            </div>
          </div>
        </div>
        `
      )
      .join('');

    container.querySelectorAll('[data-action="make-admin"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-user-id]');
        const id = card?.getAttribute('data-user-id');
        if (!id) return;
        await apiFetch(`/api/admin/users/${id}`, { method: 'POST', body: JSON.stringify({ action: 'make_admin' }) });
        allUsers = await load();
        setTotalCount(allUsers.length);
        render(allUsers);
      });
    });
    container.querySelectorAll('[data-action="remove-admin"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-user-id]');
        const id = card?.getAttribute('data-user-id');
        if (!id) return;
        await apiFetch(`/api/admin/users/${id}`, { method: 'POST', body: JSON.stringify({ action: 'remove_admin' }) });
        allUsers = await load();
        setTotalCount(allUsers.length);
        render(allUsers);
      });
    });
    container.querySelectorAll('[data-action="block"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-user-id]');
        const id = card?.getAttribute('data-user-id');
        if (!id) return;
        await apiFetch(`/api/admin/users/${id}`, { method: 'POST', body: JSON.stringify({ action: 'block' }) });
        allUsers = await load();
        setTotalCount(allUsers.length);
        render(allUsers);
      });
    });
    container.querySelectorAll('[data-action="unblock"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-user-id]');
        const id = card?.getAttribute('data-user-id');
        if (!id) return;
        await apiFetch(`/api/admin/users/${id}`, { method: 'POST', body: JSON.stringify({ action: 'unblock' }) });
        allUsers = await load();
        setTotalCount(allUsers.length);
        render(allUsers);
      });
    });
    container.querySelectorAll('[data-action="reset-profile"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const card = event.currentTarget.closest('[data-user-id]');
        const id = card?.getAttribute('data-user-id');
        if (!id) return;
        const confirmReset = window.confirm('Reset this profile? The user will need to onboard again.');
        if (!confirmReset) {
          return;
        }
        await apiFetch(`/api/admin/users/${id}`, { method: 'POST', body: JSON.stringify({ action: 'reset_profile' }) });
        allUsers = await load();
        setTotalCount(allUsers.length);
        render(allUsers);
      });
    });
  };

  const setTotalCount = (count) => {
    if (totalCount) {
      totalCount.textContent = `Total users: ${count}`;
    }
  };

  const load = async () => {
    const data = await apiFetch('/api/admin/users');
    return data;
  };

  let allUsers = [];
  try {
    allUsers = await load();
    setTotalCount(allUsers.length);
    render(allUsers);
    if (search) {
      search.addEventListener('input', () => {
        const term = search.value.trim().toLowerCase();
        if (!term) {
          render(allUsers);
          return;
        }
        const filtered = allUsers.filter((user) => {
          return user.name.toLowerCase().includes(term) || user.email.toLowerCase().includes(term);
        });
        render(filtered);
      });
    }
  } catch (error) {
    if (status) {
      status.textContent = error.message;
    }
  }
}

async function initAdminEmailTemplatesPage() {
  const select = document.getElementById('email-template-select');
  if (!select) {
    return;
  }
  const content = document.getElementById('email-template-content');
  const saveButton = document.getElementById('email-template-save');
  const status = document.getElementById('email-template-status');
  const placeholders = document.getElementById('email-template-placeholders');
  const previewFrame = document.getElementById('email-template-preview');
  let currentId = null;
  let previewTimer = null;

  const setStatus = (message) => {
    if (status) {
      status.textContent = message || '';
    }
  };

  const refreshPreview = async () => {
    if (!currentId || !previewFrame) {
      return;
    }
    try {
      const payload = { content: content?.value || '' };
      const data = await apiFetch(`/api/admin/email-templates/${currentId}/preview`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      previewFrame.srcdoc = data.html;
    } catch (error) {
      setStatus(error.message || 'Unable to preview template.');
    }
  };

  const loadTemplate = async (templateId) => {
    currentId = templateId;
    setStatus('Loading template...');
    try {
      const data = await apiFetch(`/api/admin/email-templates/${templateId}`);
      if (content) {
        content.value = data.content || '';
      }
      if (placeholders) {
        placeholders.textContent = (data.placeholders || []).map((item) => `{{${item}}}`).join(', ');
      }
      setStatus('');
      await refreshPreview();
    } catch (error) {
      setStatus(error.message || 'Unable to load template.');
    }
  };

  try {
    const templates = await apiFetch('/api/admin/email-templates');
    select.innerHTML = templates
      .map((item) => `<option value="${item.id}">${item.name}</option>`)
      .join('');
    if (templates.length) {
      await loadTemplate(templates[0].id);
    }
  } catch (error) {
    setStatus(error.message || 'Unable to load templates.');
  }

  select.addEventListener('change', async (event) => {
    const nextId = event.target.value;
    if (nextId) {
      await loadTemplate(nextId);
    }
  });

  if (content) {
    content.addEventListener('input', () => {
      window.clearTimeout(previewTimer);
      previewTimer = window.setTimeout(refreshPreview, 300);
    });
  }

  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      if (!currentId) {
        return;
      }
      setStatus('Saving...');
      try {
        await apiFetch(`/api/admin/email-templates/${currentId}`, {
          method: 'POST',
          body: JSON.stringify({ content: content?.value || '' }),
        });
        setStatus('Saved.');
      } catch (error) {
        setStatus(error.message || 'Unable to save template.');
      }
    });
  }
}

async function initAdminStoriesPage() {
  const list = document.getElementById('admin-story-list');
  if (!list) {
    return;
  }
  const saveButton = document.getElementById('admin-stories-save');
  const status = document.getElementById('admin-stories-status');

  try {
    const me = await apiFetch('/api/users/me');
    if (me.role !== 'ADMIN') {
      window.location.href = '/dashboard';
      return;
    }
  } catch (error) {
    window.location.href = '/authentication';
    return;
  }

  const escapeHtml = (value) => {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  const normalize = (items) => {
    const base = items && items.length ? items.slice(0, 4) : [];
    while (base.length < 4) {
      base.push({ title: '', image: '', description: '', link: '' });
    }
    return base;
  };

  const render = (items) => {
    const stories = normalize(items);
    list.innerHTML = stories
      .map(
        (story, index) => `
        <div class="border border-warm-gray bg-white p-6" data-story-index="${index}">
          <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">Story ${index + 1}</p>
          <div class="mt-4 grid gap-4 md:grid-cols-2">
            <label class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-400">
              Title
              <input class="mt-2 w-full border border-warm-gray px-3 py-2 text-sm bg-white" data-field="title" value="${escapeHtml(story.title)}" />
            </label>
            <label class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-400">
              Image URL
              <input class="mt-2 w-full border border-warm-gray px-3 py-2 text-sm bg-white" data-field="image" value="${escapeHtml(story.image)}" />
            </label>
            <label class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-400 md:col-span-2">
              Redirect Link
              <input class="mt-2 w-full border border-warm-gray px-3 py-2 text-sm bg-white" data-field="link" value="${escapeHtml(story.link)}" />
            </label>
          </div>
          <label class="mt-4 block text-xs font-semibold uppercase tracking-[0.2em] text-gray-400">
            Description
            <textarea class="mt-2 w-full min-h-[120px] border border-warm-gray px-3 py-2 text-sm bg-white" data-field="description">${escapeHtml(story.description)}</textarea>
          </label>
        </div>
      `
      )
      .join('');
  };

  const load = async () => {
    const data = await apiFetch('/api/admin/stories');
    render(data.items || []);
  };

  try {
    await load();
  } catch (error) {
    if (status) {
      status.textContent = error.message || 'Unable to load stories.';
    }
  }

  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      const cards = Array.from(list.querySelectorAll('[data-story-index]'));
      const items = cards.map((card) => {
        const title = card.querySelector('[data-field="title"]')?.value?.trim() || '';
        const image = card.querySelector('[data-field="image"]')?.value?.trim() || '';
        const description = card.querySelector('[data-field="description"]')?.value?.trim() || '';
        const link = card.querySelector('[data-field="link"]')?.value?.trim() || '';
        return { title, image, description, link };
      });
      if (items.some((item) => !item.title || !item.image || !item.description || !item.link)) {
        if (status) {
          status.textContent = 'Please fill in title, image, description, and link for all four stories.';
        }
        return;
      }
      if (status) {
        status.textContent = 'Saving stories...';
      }
      try {
        await apiFetch('/api/admin/stories', {
          method: 'PUT',
          body: JSON.stringify({ items }),
        });
        if (status) {
          status.textContent = 'Stories saved.';
        }
      } catch (error) {
        if (status) {
          status.textContent = error.message || 'Unable to save stories.';
        }
      }
    });
  }
}

async function initPrefectEmailTemplatesPage() {
  const select = document.getElementById('mentor-email-template-select');
  if (!select) {
    return;
  }
  const content = document.getElementById('mentor-email-template-content');
  const saveButton = document.getElementById('mentor-email-template-save');
  const status = document.getElementById('mentor-email-template-status');
  const placeholders = document.getElementById('mentor-email-template-placeholders');
  const previewFrame = document.getElementById('mentor-email-template-preview');
  let currentId = null;
  let previewTimer = null;

  const setStatus = (message) => {
    if (status) {
      status.textContent = message || '';
    }
  };

  const refreshPreview = async () => {
    if (!currentId || !previewFrame) {
      return;
    }
    try {
      const payload = { content: content?.value || '' };
      const data = await apiFetch(`/api/mentors/email-templates/${currentId}/preview`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      previewFrame.srcdoc = data.html;
    } catch (error) {
      setStatus(error.message || 'Unable to preview template.');
    }
  };

  const loadTemplate = async (templateId) => {
    currentId = templateId;
    setStatus('Loading template...');
    try {
      const data = await apiFetch(`/api/mentors/email-templates/${templateId}`);
      if (content) {
        content.value = data.content || '';
      }
      if (placeholders) {
        placeholders.textContent = (data.placeholders || []).map((item) => `{{${item}}}`).join(', ');
      }
      setStatus('');
      await refreshPreview();
    } catch (error) {
      setStatus(error.message || 'Unable to load template.');
    }
  };

  try {
    const templates = await apiFetch('/api/mentors/email-templates');
    select.innerHTML = templates
      .map((item) => `<option value="${item.id}">${item.name}</option>`)
      .join('');
    if (templates.length) {
      await loadTemplate(templates[0].id);
    }
  } catch (error) {
    setStatus(error.message || 'Unable to load templates.');
  }

  select.addEventListener('change', async (event) => {
    const nextId = event.target.value;
    if (nextId) {
      await loadTemplate(nextId);
    }
  });

  if (content) {
    content.addEventListener('input', () => {
      window.clearTimeout(previewTimer);
      previewTimer = window.setTimeout(refreshPreview, 300);
    });
  }

  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      if (!currentId) {
        return;
      }
      setStatus('Saving...');
      try {
        await apiFetch(`/api/mentors/email-templates/${currentId}`, {
          method: 'POST',
          body: JSON.stringify({ content: content?.value || '' }),
        });
        setStatus('Saved.');
      } catch (error) {
        setStatus(error.message || 'Unable to save template.');
      }
    });
  }
}
async function initPrefectDashboardPage() {
  const container = document.getElementById('mentor-requests');
  const status = document.getElementById('mentor-requests-status');
  const studentsContainer = document.getElementById('mentor-students');
  const studentsCount = document.getElementById('mentor-students-count');
  if (!container) {
    return;
  }

  try {
    const status = await apiFetch('/api/onboarding/status');
    if (status.role !== 'MENTOR') {
      window.location.href = '/dashboard';
      return;
    }
    if (!status.mentor_approved) {
      window.location.href = '/mentor/pending';
      return;
    }
  } catch (error) {
    window.location.href = '/authentication';
    return;
  }

  try {
    const requests = await apiFetch('/api/requests/incoming');
    const pendingRequests = requests.filter((req) => req.type === 'MENTORSHIP' && req.status === 'PENDING');
    if (!pendingRequests.length) {
      container.innerHTML = `
        <div class="border border-warm-gray bg-white/70 p-6 text-center">
          <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No requests yet</p>
          <p class="text-sm text-gray-500 mt-2">You will see mentorship requests here.</p>
        </div>
      `;
    } else {
      container.innerHTML = pendingRequests.map((req) => `
        <div class="border border-warm-gray bg-white p-6" data-request-id="${req.id}">
          <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div>
              <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">${req.status}</p>
              <h3 class="text-2xl text-primary mt-2">${req.counterpart_name}</h3>
              <p class="text-sm text-gray-500 mt-2">${req.message}</p>
              ${req.counterpart_email ? `<p class="text-xs text-gray-400 mt-2">Email: ${req.counterpart_email}</p>` : ''}
            </div>
            <div class="flex gap-3">
              <button class="border border-primary text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="accept">Accept</button>
              <button class="border border-warm-gray text-[10px] font-semibold uppercase tracking-[0.3em] px-4 py-2" data-action="reject">Reject</button>
            </div>
          </div>
        </div>
      `).join('');

      container.querySelectorAll('[data-action="accept"]').forEach((button) => {
        button.addEventListener('click', async (event) => {
          const card = event.currentTarget.closest('[data-request-id]');
          const id = card?.getAttribute('data-request-id');
          if (!id) return;
          await apiFetch(`/api/requests/${id}/accept`, { method: 'POST' });
          await initPrefectDashboardPage();
        });
      });
      container.querySelectorAll('[data-action="reject"]').forEach((button) => {
        button.addEventListener('click', async (event) => {
          const card = event.currentTarget.closest('[data-request-id]');
          const id = card?.getAttribute('data-request-id');
          if (!id) return;
          await apiFetch(`/api/requests/${id}/reject`, { method: 'POST' });
          await initPrefectDashboardPage();
        });
      });
    }

    if (studentsContainer) {
      const accepted = requests.filter((req) => req.type === 'MENTORSHIP' && req.status === 'ACCEPTED');
      if (studentsCount) {
        studentsCount.textContent = `${accepted.length} students`;
      }
      studentsContainer.innerHTML = accepted.length
        ? accepted.map((req) => `
          <div class="border border-warm-gray bg-white p-6">
            <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">Accepted</p>
            <h3 class="text-2xl text-primary mt-2">${req.counterpart_name}</h3>
            <p class="text-sm text-gray-500 mt-2">${req.message || ''}</p>
            ${req.counterpart_email ? `<p class="text-xs text-gray-400 mt-2">Email: ${req.counterpart_email}</p>` : ''}
          </div>
        `).join('')
        : `
          <div class="border border-warm-gray bg-white/70 p-6 text-center">
            <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-400">No accepted students yet</p>
            <p class="text-sm text-gray-500 mt-2">Accept a request to start mentoring.</p>
          </div>
        `;
    }
  } catch (error) {
    if (status) {
      status.textContent = error.message;
    }
  }
}

async function initPrefectPendingPage() {
  const marker = document.querySelector('[data-mentor-pending]');
  if (!marker) {
    return;
  }

  const checkStatus = async () => {
    try {
      const status = await apiFetch('/api/onboarding/status');
      if (status.role !== 'MENTOR') {
        window.location.href = '/dashboard';
        return;
      }
      if (status.mentor_approved) {
        window.location.href = '/mentor/dashboard';
        return;
      }
      window.setTimeout(checkStatus, 4000);
    } catch (error) {
      window.setTimeout(checkStatus, 4000);
    }
  };

  checkStatus();
}

document.addEventListener('DOMContentLoaded', () => {
  initFontLoading();
  initMobileNav();
  initOnboardingGuard();
  initGlobalNav();
  initMainDashboardStories();
  initAuthPage();
  initDashboardPage();
  initProfilePage();
  initProfileSetupPage();
  initRoleSelectionPage();
  initPrefectRequestPage();
  initRequestMessagePage();
  initPrefectSetupPage();
  initAdminPrefectsPage();
  initAdminUsersPage();
  initAdminEmailTemplatesPage();
  initAdminStoriesPage();
  initPrefectEmailTemplatesPage();
  initPrefectDashboardPage();
  initPrefectPendingPage();
  initPrefectsPage();
  initRequestsPage();
  initLogoutButtons();
  initMobileNav();
});
