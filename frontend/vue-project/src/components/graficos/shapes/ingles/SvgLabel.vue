<template>
  <g :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ============================================ -->
    <!--     CLOTHING (ROPA)                         -->
    <!-- ============================================ -->

    <!-- CLOTHING: WASH LABEL -->
    <g v-if="type === 'clothing-wash-label'">
      <path d="M20,10 L180,10 L180,260 L100,280 L20,260 Z" fill="#f5f5f0" stroke="#d4d4d0" stroke-width="2"/>
      <line x1="20" y1="15" x2="180" y2="15" stroke="#ccc" stroke-width="1" stroke-dasharray="4,2"/>
      <text x="100" y="40" text-anchor="middle" font-family="Georgia, serif" font-size="14" font-weight="bold" fill="#333">FASHION Co.</text>
      <line x1="40" y1="55" x2="160" y2="55" stroke="#ddd" stroke-width="1"/>
      <text x="100" y="75" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">100% COTTON</text>
      <g transform="translate(35, 90)">
        <g transform="translate(0, 0)">
          <path d="M0,20 Q15,-5 30,20 Z" fill="none" stroke="#333" stroke-width="1.5"/>
          <text x="15" y="15" text-anchor="middle" font-family="Arial" font-size="8" fill="#333">30°</text>
        </g>
        <g transform="translate(40, 0)">
          <polygon points="15,0 30,20 0,20" fill="none" stroke="#333" stroke-width="1.5"/>
          <line x1="5" y1="5" x2="25" y2="18" stroke="#333" stroke-width="1.5"/>
        </g>
        <g transform="translate(80, 0)">
          <path d="M0,18 L5,5 L25,5 L30,18 Z" fill="none" stroke="#333" stroke-width="1.5"/>
          <circle cx="15" cy="13" r="2" fill="#333"/>
          <circle cx="10" cy="13" r="2" fill="#333"/>
        </g>
        <g transform="translate(120, 0)">
          <rect x="0" y="2" width="25" height="18" rx="2" fill="none" stroke="#333" stroke-width="1.5"/>
          <circle cx="12" cy="11" r="5" fill="none" stroke="#333" stroke-width="1"/>
          <line x1="3" y1="3" x2="22" y2="18" stroke="#333" stroke-width="1.5"/>
        </g>
      </g>
      <g transform="translate(100, 135)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">MACHINE WASH COLD</text>
        <text x="0" y="14" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">DO NOT BLEACH</text>
        <text x="0" y="28" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">MEDIUM IRON</text>
        <text x="0" y="42" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">DO NOT TUMBLE DRY</text>
      </g>
      <rect x="70" y="195" width="60" height="30" rx="4" fill="#333"/>
      <text x="100" y="215" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="#fff">M</text>
      <text x="100" y="250" text-anchor="middle" font-family="Arial" font-size="8" fill="#999">MADE IN PORTUGAL</text>
    </g>

    <!-- CLOTHING: SIZE LABEL -->
    <g v-if="type === 'clothing-size-label'">
      <rect x="10" y="10" width="100" height="140" rx="4" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="60" cy="25" r="8" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>
      <text x="60" y="55" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="12" fill="#333">URBAN</text>
      <text x="60" y="68" text-anchor="middle" font-family="Arial" font-size="8" fill="#666">STYLE</text>
      <text x="60" y="105" text-anchor="middle" font-family="Arial" font-size="36" font-weight="bold" fill="#333">XL</text>
      <text x="60" y="125" text-anchor="middle" font-family="Arial" font-size="10" fill="#999">EU 44 / US 14</text>
      <text x="60" y="145" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#e74c3c">$29.99</text>
    </g>

    <!-- ============================================ -->
    <!--     FOOD (ALIMENTOS)                        -->
    <!-- ============================================ -->

    <!-- FOOD: NUTRITION LABEL -->
    <g v-if="type === 'food-nutrition-label'">
      <rect x="10" y="10" width="200" height="300" fill="#ffffff" stroke="#000" stroke-width="2"/>
      <text x="110" y="35" text-anchor="middle" font-family="Arial Black" font-size="18" fill="#000">Nutrition Facts</text>
      <rect x="15" y="42" width="190" height="8" fill="#000"/>
      <text x="20" y="65" font-family="Arial" font-size="10" fill="#000">Serving Size 1 cup (240ml)</text>
      <text x="20" y="78" font-family="Arial" font-size="10" fill="#000">Servings Per Container 4</text>
      <rect x="15" y="85" width="190" height="4" fill="#000"/>
      <text x="20" y="105" font-family="Arial Black" font-size="12" fill="#000">Calories</text>
      <text x="180" y="105" text-anchor="end" font-family="Arial Black" font-size="18" fill="#000">120</text>
      <line x1="15" y1="112" x2="205" y2="112" stroke="#000" stroke-width="1"/>
      <text x="200" y="125" text-anchor="end" font-family="Arial" font-size="9" fill="#000">% Daily Value*</text>
      <g font-family="Arial" font-size="10" fill="#000">
        <line x1="15" y1="132" x2="205" y2="132" stroke="#000" stroke-width="1"/>
        <text x="20" y="145"><tspan font-weight="bold">Total Fat</tspan> 2g</text>
        <text x="200" y="145" text-anchor="end">3%</text>
        <line x1="15" y1="152" x2="205" y2="152" stroke="#000" stroke-width="1"/>
        <text x="35" y="165">Saturated Fat 0.5g</text>
        <text x="200" y="165" text-anchor="end">3%</text>
        <line x1="15" y1="172" x2="205" y2="172" stroke="#000" stroke-width="1"/>
        <text x="20" y="185"><tspan font-weight="bold">Cholesterol</tspan> 5mg</text>
        <text x="200" y="185" text-anchor="end">2%</text>
        <line x1="15" y1="192" x2="205" y2="192" stroke="#000" stroke-width="1"/>
        <text x="20" y="205"><tspan font-weight="bold">Sodium</tspan> 120mg</text>
        <text x="200" y="205" text-anchor="end">5%</text>
        <line x1="15" y1="212" x2="205" y2="212" stroke="#000" stroke-width="1"/>
        <text x="20" y="225"><tspan font-weight="bold">Total Carbs</tspan> 22g</text>
        <text x="200" y="225" text-anchor="end">8%</text>
        <line x1="15" y1="232" x2="205" y2="232" stroke="#000" stroke-width="1"/>
        <text x="35" y="245">Dietary Fiber 0g</text>
        <text x="200" y="245" text-anchor="end">0%</text>
        <line x1="15" y1="252" x2="205" y2="252" stroke="#000" stroke-width="1"/>
        <text x="35" y="265">Total Sugars 18g</text>
        <line x1="15" y1="272" x2="205" y2="272" stroke="#000" stroke-width="1"/>
        <text x="20" y="285"><tspan font-weight="bold">Protein</tspan> 8g</text>
      </g>
      <rect x="15" y="292" width="190" height="4" fill="#000"/>
    </g>

    <!-- FOOD: KEEP FROZEN -->
    <g v-if="type === 'food-keep-frozen'">
      <rect x="10" y="10" width="180" height="100" rx="8" fill="#e8f4f8" stroke="#3498db" stroke-width="3"/>
      <g transform="translate(50, 55)">
        <line x1="0" y1="-20" x2="0" y2="20" stroke="#3498db" stroke-width="3"/>
        <line x1="-17" y1="-10" x2="17" y2="10" stroke="#3498db" stroke-width="3"/>
        <line x1="-17" y1="10" x2="17" y2="-10" stroke="#3498db" stroke-width="3"/>
        <circle cx="0" cy="0" r="5" fill="#3498db"/>
        <line x1="0" y1="-20" x2="-5" y2="-15" stroke="#3498db" stroke-width="2"/>
        <line x1="0" y1="-20" x2="5" y2="-15" stroke="#3498db" stroke-width="2"/>
        <line x1="0" y1="20" x2="-5" y2="15" stroke="#3498db" stroke-width="2"/>
        <line x1="0" y1="20" x2="5" y2="15" stroke="#3498db" stroke-width="2"/>
      </g>
      <g transform="translate(130, 45)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#2980b9">KEEP</text>
        <text x="0" y="15" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#2980b9">FROZEN</text>
        <text x="0" y="32" text-anchor="middle" font-family="Arial" font-size="10" fill="#3498db">-18°C / 0°F</text>
      </g>
      <rect x="15" y="15" width="170" height="90" rx="5" fill="none" stroke="#3498db" stroke-width="1" stroke-dasharray="5,3"/>
    </g>

    <!-- FOOD: REFRIGERATE -->
    <g v-if="type === 'food-refrigerate'">
      <rect x="10" y="10" width="180" height="80" rx="6" fill="#fff3e0" stroke="#e67e22" stroke-width="2"/>
      <g transform="translate(40, 50)">
        <rect x="-18" y="-25" width="36" height="50" rx="3" fill="none" stroke="#e67e22" stroke-width="2"/>
        <line x1="-18" y1="-5" x2="18" y2="-5" stroke="#e67e22" stroke-width="2"/>
        <rect x="12" y="-18" width="4" height="8" rx="1" fill="#e67e22"/>
        <rect x="12" y="2" width="4" height="8" rx="1" fill="#e67e22"/>
      </g>
      <g transform="translate(130, 40)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="#d35400">REFRIGERATE</text>
        <text x="0" y="14" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="#d35400">AFTER OPENING</text>
        <text x="0" y="30" text-anchor="middle" font-family="Arial" font-size="9" fill="#e67e22">Use within 5 days</text>
      </g>
    </g>

    <!-- FOOD: BEST BEFORE -->
    <g v-if="type === 'food-best-before'">
      <rect x="10" y="10" width="160" height="60" rx="4" fill="#ffffff" stroke="#333" stroke-width="2"/>
      <text x="90" y="32" text-anchor="middle" font-family="Arial" font-size="11" fill="#666">BEST BEFORE</text>
      <text x="90" y="55" text-anchor="middle" font-family="monospace" font-size="18" font-weight="bold" fill="#333">15 MAR 2026</text>
      <rect x="15" y="15" width="150" height="50" rx="2" fill="none" stroke="#ccc" stroke-width="1" stroke-dasharray="3,2"/>
    </g>

    <!-- FOOD: USE BY -->
    <g v-if="type === 'food-use-by'">
      <rect x="10" y="10" width="160" height="60" rx="4" fill="#ffebee" stroke="#c0392b" stroke-width="2"/>
      <text x="90" y="32" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#c0392b">USE BY</text>
      <text x="90" y="55" text-anchor="middle" font-family="monospace" font-size="18" font-weight="bold" fill="#c0392b">08 JAN 2026</text>
    </g>

    <!-- ============================================ -->
    <!--     MEDICINE (MEDICINA)                     -->
    <!-- ============================================ -->

    <!-- MEDICINE: DOSAGE -->
    <g v-if="type === 'medicine-dosage'">
      <rect x="10" y="10" width="220" height="160" rx="8" fill="#ffffff" stroke="#27ae60" stroke-width="3"/>
      <rect x="10" y="10" width="220" height="35" rx="8" fill="#27ae60"/>
      <rect x="10" y="30" width="220" height="15" fill="#27ae60"/>
      <text x="120" y="33" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">DOSAGE INSTRUCTIONS</text>
      <g transform="translate(45, 80)">
        <ellipse cx="0" cy="0" rx="20" ry="12" fill="#3498db"/>
        <ellipse cx="-10" cy="0" rx="10" ry="12" fill="#2980b9"/>
      </g>
      <g transform="translate(80, 65)">
        <text x="0" y="0" font-family="Arial" font-size="11" fill="#333">Adults: 1-2 tablets</text>
        <text x="0" y="18" font-family="Arial" font-size="11" fill="#333">every 4-6 hours</text>
        <text x="0" y="40" font-family="Arial" font-size="10" fill="#666">Maximum: 8 tablets in 24h</text>
      </g>
      <g transform="translate(120, 135)">
        <rect x="-100" y="-12" width="200" height="30" rx="4" fill="#fff3cd"/>
        <text x="0" y="5" text-anchor="middle" font-family="Arial" font-size="9" fill="#856404">⚠️ Do not exceed recommended dose</text>
      </g>
    </g>

    <!-- MEDICINE: WARNING -->
    <g v-if="type === 'medicine-warning'">
      <rect x="10" y="10" width="180" height="120" rx="8" fill="#fff9c4" stroke="#f39c12" stroke-width="3"/>
      <g transform="translate(100, 50)">
        <polygon points="0,-25 28,20 -28,20" fill="#f39c12"/>
        <text x="0" y="12" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="#fff">!</text>
      </g>
      <text x="100" y="95" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#333">MAY CAUSE DROWSINESS</text>
      <text x="100" y="112" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">Do not drive or operate machinery</text>
    </g>

    <!-- MEDICINE: KEEP AWAY CHILDREN -->
    <g v-if="type === 'medicine-keep-away-children'">
      <rect x="10" y="10" width="180" height="100" rx="6" fill="#ffffff" stroke="#e74c3c" stroke-width="3"/>
      <g transform="translate(55, 55)">
        <circle cx="0" cy="-15" r="10" fill="#333"/>
        <line x1="0" y1="-5" x2="0" y2="15" stroke="#333" stroke-width="3"/>
        <line x1="-12" y1="0" x2="12" y2="0" stroke="#333" stroke-width="3"/>
        <line x1="0" y1="15" x2="-8" y2="28" stroke="#333" stroke-width="3"/>
        <line x1="0" y1="15" x2="8" y2="28" stroke="#333" stroke-width="3"/>
        <circle cx="0" cy="5" r="30" fill="none" stroke="#e74c3c" stroke-width="3"/>
        <line x1="-22" y1="-17" x2="22" y2="27" stroke="#e74c3c" stroke-width="3"/>
      </g>
      <g transform="translate(145, 45)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="9" font-weight="bold" fill="#c0392b">KEEP OUT OF</text>
        <text x="0" y="13" text-anchor="middle" font-family="Arial" font-size="9" font-weight="bold" fill="#c0392b">REACH OF</text>
        <text x="0" y="26" text-anchor="middle" font-family="Arial" font-size="9" font-weight="bold" fill="#c0392b">CHILDREN</text>
      </g>
    </g>

    <!-- ============================================ -->
    <!--     CLEANING (LIMPIEZA)                     -->
    <!-- ============================================ -->

    <!-- CLEANING: HAZARD -->
    <g v-if="type === 'cleaning-hazard'">
      <rect x="10" y="10" width="180" height="180" rx="8" fill="#ffffff" stroke="#333" stroke-width="2"/>
      <g transform="translate(100, 85)">
        <polygon points="0,-55 55,0 0,55 -55,0" fill="#ffffff" stroke="#e74c3c" stroke-width="3"/>
        <g transform="translate(0, -5)">
          <path d="M-15,-15 L-5,-15 L-5,5 L-15,15" fill="none" stroke="#333" stroke-width="2"/>
          <ellipse cx="0" cy="-25" rx="8" ry="5" fill="#333"/>
          <path d="M0,-20 L-3,-10 L3,-10 Z" fill="#333"/>
          <path d="M-10,15 Q0,25 10,15" fill="none" stroke="#333" stroke-width="2"/>
          <line x1="-8" y1="18" x2="-5" y2="25" stroke="#333" stroke-width="1"/>
          <line x1="0" y1="20" x2="0" y2="27" stroke="#333" stroke-width="1"/>
          <line x1="8" y1="18" x2="5" y2="25" stroke="#333" stroke-width="1"/>
        </g>
      </g>
      <text x="100" y="160" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#c0392b">CORROSIVE</text>
      <text x="100" y="178" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">Causes severe burns</text>
    </g>

    <!-- CLEANING: INSTRUCTIONS -->
    <g v-if="type === 'cleaning-instructions'">
      <rect x="10" y="10" width="200" height="140" rx="6" fill="#e8f5e9" stroke="#27ae60" stroke-width="2"/>
      <rect x="10" y="10" width="200" height="30" fill="#27ae60" rx="6"/>
      <rect x="10" y="25" width="200" height="15" fill="#27ae60"/>
      <text x="110" y="30" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#ffffff">DIRECTIONS FOR USE</text>
      <g transform="translate(25, 55)" font-family="Arial" font-size="10" fill="#333">
        <circle cx="8" cy="5" r="8" fill="#27ae60"/>
        <text x="8" y="9" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">1</text>
        <text x="25" y="9">Dilute 1 cap in 5L water</text>
        <circle cx="8" cy="35" r="8" fill="#27ae60"/>
        <text x="8" y="39" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">2</text>
        <text x="25" y="39">Apply with cloth or mop</text>
        <circle cx="8" cy="65" r="8" fill="#27ae60"/>
        <text x="8" y="69" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">3</text>
        <text x="25" y="69">Leave for 5 minutes</text>
        <circle cx="8" cy="95" r="8" fill="#27ae60"/>
        <text x="8" y="99" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold">4</text>
        <text x="25" y="99">Rinse with clean water</text>
      </g>
    </g>

    <!-- ============================================ -->
    <!--     PRODUCT (PRODUCTOS GENÉRICOS)           -->
    <!-- ============================================ -->

    <!-- PRODUCT: BARCODE -->
    <g v-if="type === 'product-barcode'">
      <rect x="10" y="10" width="180" height="80" fill="#ffffff" stroke="#ddd" stroke-width="1"/>
      <g transform="translate(30, 20)">
        <rect x="0" y="0" width="2" height="45" fill="#000"/>
        <rect x="4" y="0" width="1" height="45" fill="#000"/>
        <rect x="7" y="0" width="3" height="45" fill="#000"/>
        <rect x="12" y="0" width="1" height="45" fill="#000"/>
        <rect x="15" y="0" width="2" height="45" fill="#000"/>
        <rect x="20" y="0" width="1" height="45" fill="#000"/>
        <rect x="23" y="0" width="3" height="45" fill="#000"/>
        <rect x="28" y="0" width="2" height="45" fill="#000"/>
        <rect x="32" y="0" width="1" height="45" fill="#000"/>
        <rect x="36" y="0" width="2" height="45" fill="#000"/>
        <rect x="40" y="0" width="1" height="45" fill="#000"/>
        <rect x="43" y="0" width="3" height="45" fill="#000"/>
        <rect x="48" y="0" width="1" height="45" fill="#000"/>
        <rect x="52" y="0" width="2" height="45" fill="#000"/>
        <rect x="56" y="0" width="1" height="45" fill="#000"/>
        <rect x="60" y="0" width="3" height="45" fill="#000"/>
        <rect x="65" y="0" width="2" height="45" fill="#000"/>
        <rect x="70" y="0" width="1" height="45" fill="#000"/>
        <rect x="74" y="0" width="2" height="45" fill="#000"/>
        <rect x="78" y="0" width="3" height="45" fill="#000"/>
        <rect x="83" y="0" width="1" height="45" fill="#000"/>
        <rect x="87" y="0" width="2" height="45" fill="#000"/>
        <rect x="92" y="0" width="1" height="45" fill="#000"/>
        <rect x="96" y="0" width="3" height="45" fill="#000"/>
        <rect x="102" y="0" width="1" height="45" fill="#000"/>
        <rect x="106" y="0" width="2" height="45" fill="#000"/>
        <rect x="112" y="0" width="1" height="45" fill="#000"/>
        <rect x="116" y="0" width="3" height="45" fill="#000"/>
        <rect x="122" y="0" width="2" height="45" fill="#000"/>
        <rect x="127" y="0" width="1" height="45" fill="#000"/>
        <rect x="130" y="0" width="3" height="45" fill="#000"/>
        <rect x="136" y="0" width="2" height="45" fill="#000"/>
        <rect x="140" y="0" width="1" height="45" fill="#000"/>
      </g>
      <text x="100" y="78" text-anchor="middle" font-family="monospace" font-size="11" fill="#000">5 901234 123457</text>
    </g>

    <!-- PRODUCT: QR CODE -->
    <g v-if="type === 'product-qr-code'">
      <rect x="10" y="10" width="130" height="160" rx="6" fill="#ffffff" stroke="#ddd" stroke-width="2"/>
      <g transform="translate(30, 25)">
        <rect x="0" y="0" width="25" height="25" fill="#000"/>
        <rect x="5" y="5" width="15" height="15" fill="#fff"/>
        <rect x="8" y="8" width="9" height="9" fill="#000"/>
        <rect x="65" y="0" width="25" height="25" fill="#000"/>
        <rect x="70" y="5" width="15" height="15" fill="#fff"/>
        <rect x="73" y="8" width="9" height="9" fill="#000"/>
        <rect x="0" y="65" width="25" height="25" fill="#000"/>
        <rect x="5" y="70" width="15" height="15" fill="#fff"/>
        <rect x="8" y="73" width="9" height="9" fill="#000"/>
        <rect x="30" y="5" width="5" height="5" fill="#000"/>
        <rect x="40" y="5" width="5" height="5" fill="#000"/>
        <rect x="50" y="10" width="5" height="5" fill="#000"/>
        <rect x="30" y="15" width="5" height="5" fill="#000"/>
        <rect x="45" y="20" width="5" height="5" fill="#000"/>
        <rect x="5" y="30" width="5" height="5" fill="#000"/>
        <rect x="15" y="35" width="5" height="5" fill="#000"/>
        <rect x="25" y="30" width="5" height="5" fill="#000"/>
        <rect x="35" y="40" width="5" height="5" fill="#000"/>
        <rect x="50" y="35" width="5" height="5" fill="#000"/>
        <rect x="60" y="30" width="5" height="5" fill="#000"/>
        <rect x="75" y="35" width="5" height="5" fill="#000"/>
        <rect x="85" y="40" width="5" height="5" fill="#000"/>
        <rect x="30" y="50" width="5" height="5" fill="#000"/>
        <rect x="45" y="55" width="5" height="5" fill="#000"/>
        <rect x="55" y="50" width="5" height="5" fill="#000"/>
        <rect x="70" y="55" width="5" height="5" fill="#000"/>
        <rect x="85" y="50" width="5" height="5" fill="#000"/>
        <rect x="30" y="65" width="5" height="5" fill="#000"/>
        <rect x="40" y="70" width="5" height="5" fill="#000"/>
        <rect x="55" y="65" width="5" height="5" fill="#000"/>
        <rect x="65" y="75" width="5" height="5" fill="#000"/>
        <rect x="80" y="70" width="5" height="5" fill="#000"/>
        <rect x="85" y="80" width="5" height="5" fill="#000"/>
        <rect x="30" y="80" width="5" height="5" fill="#000"/>
        <rect x="45" y="85" width="5" height="5" fill="#000"/>
        <rect x="60" y="80" width="5" height="5" fill="#000"/>
        <rect x="75" y="85" width="5" height="5" fill="#000"/>
      </g>
      <text x="75" y="145" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">SCAN FOR</text>
      <text x="75" y="158" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">MORE INFO</text>
    </g>

    <!-- PRODUCT: PRICE TAG -->
    <g v-if="type === 'price-tag'">
      <path d="M10,20 L130,20 L150,50 L130,80 L10,80 Z" fill="#e74c3c" stroke="#c0392b" stroke-width="2"/>
      <circle cx="25" cy="50" r="8" fill="#ffffff"/>
      <text x="85" y="42" text-anchor="middle" font-family="Arial" font-size="10" fill="#ffffff">NOW ONLY</text>
      <text x="85" y="68" text-anchor="middle" font-family="Arial Black" font-size="26" fill="#ffffff">$9.99</text>
    </g>

    <!-- PRODUCT: SALE TAG -->
    <g v-if="type === 'sale-tag'">
      <polygon 
        points="75,5 85,35 115,25 100,50 130,60 100,75 120,100 90,90 75,120 60,90 30,100 50,75 20,60 50,50 35,25 65,35"
        fill="#f1c40f"
        stroke="#d4a800"
        stroke-width="2"
      />
      <circle cx="75" cy="65" r="40" fill="#e74c3c"/>
      <text x="75" y="55" text-anchor="middle" font-family="Arial Black" font-size="18" fill="#ffffff">SALE</text>
      <text x="75" y="78" text-anchor="middle" font-family="Arial Black" font-size="20" fill="#ffffff">50%</text>
      <text x="75" y="92" text-anchor="middle" font-family="Arial" font-size="10" fill="#ffffff">OFF</text>
    </g>

    <!-- PRODUCT: ORGANIC LABEL -->
    <g v-if="type === 'organic-label'">
      <circle cx="80" cy="80" r="70" fill="#27ae60" stroke="#1e8449" stroke-width="3"/>
      <circle cx="80" cy="80" r="55" fill="#2ecc71"/>
      <g transform="translate(80, 65)">
        <path d="M0,-25 Q25,-15 25,10 Q15,30 0,25 Q-15,30 -25,10 Q-25,-15 0,-25" fill="#27ae60"/>
        <path d="M0,-20 Q0,5 0,20" fill="none" stroke="#1e8449" stroke-width="2"/>
        <path d="M-12,-5 Q0,0 0,5" fill="none" stroke="#1e8449" stroke-width="1.5"/>
        <path d="M12,-5 Q0,0 0,5" fill="none" stroke="#1e8449" stroke-width="1.5"/>
      </g>
      <text x="80" y="115" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">ORGANIC</text>
      <text x="80" y="132" text-anchor="middle" font-family="Arial" font-size="9" fill="#ffffff">100% NATURAL</text>
    </g>

    <!-- PRODUCT: FRAGILE LABEL -->
    <g v-if="type === 'fragile-label'">
      <rect x="10" y="10" width="160" height="100" rx="4" fill="#ffffff" stroke="#e74c3c" stroke-width="3"/>
      <g transform="translate(55, 55)">
        <path d="M-15,-25 L-10,-25 L-5,0 L-10,5 L-10,15 L-18,15 L-18,20 L2,20 L2,15 L-5,15 L-5,5 L0,0 L5,-25 L10,-25" 
              fill="none" stroke="#333" stroke-width="2" stroke-linejoin="round"/>
        <path d="M-8,-20 L-3,-10 L-8,0" fill="none" stroke="#e74c3c" stroke-width="2"/>
      </g>
      <g transform="translate(130, 45)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial Black" font-size="14" fill="#e74c3c">FRAGILE</text>
        <text x="0" y="18" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">Handle</text>
        <text x="0" y="30" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">with care</text>
      </g>
    </g>

    <!-- PRODUCT: THIS SIDE UP -->
    <g v-if="type === 'this-side-up'">
      <rect x="10" y="10" width="130" height="130" rx="4" fill="#ffffff" stroke="#333" stroke-width="2"/>
      <g transform="translate(75, 60)">
        <polygon points="-30,20 0,-20 30,20 15,20 15,40 -15,40 -15,20" fill="#333"/>
      </g>
      <line x1="30" y1="110" x2="120" y2="110" stroke="#333" stroke-width="3"/>
      <text x="75" y="130" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#333">THIS SIDE UP</text>
    </g>

    <!-- Label opcional -->
    <text
      v-if="label"
      x="100"
      y="240"
      font-family="sans-serif"
      font-size="14"
      font-weight="bold"
      fill="#374151"
      text-anchor="middle"
    >
      {{ label }}
    </text>

  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  width: { type: Number, default: 200 }, // Ancho base estándar
  type: { type: String, default: 'clothing-wash-label' },
  label: { type: String, default: '' }
});

// Calculamos escala basada en el ancho deseado
const scale = computed(() => {
  return props.width / 200;
});
</script>
