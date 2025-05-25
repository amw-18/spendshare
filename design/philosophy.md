# SpendShare Design Philosophy

This document outlines the design philosophy, visual language, and component guidelines for the SpendShare application, derived from the `design/landing.html` example. The goal is to ensure a consistent, modern, and user-friendly experience across the platform.

## 1. Core Principles

*   **Modern & Sleek:** Embrace a contemporary dark-themed aesthetic that feels professional and trustworthy.
*   **Clarity & Simplicity:** Prioritize ease of use. Information should be presented clearly, and user flows should be intuitive.
*   **User-Centric:** Design with the user's needs and goals in mind, focusing on solving their expense-sharing problems efficiently.
*   **Consistent Experience:** Maintain a uniform look and feel across all parts of the application, from landing pages to internal dashboards.
*   **Responsive & Accessible:** Ensure the application is usable and performs well on all device sizes. Strive for accessibility best practices.
*   **Trust & Security:** The design should visually reinforce the security and reliability of the platform, especially given its financial nature.

## 2. Visual Language

### 2.1. Color Palette

*   **Primary Backgrounds:** Deep, dark purples and indigos create a sophisticated and focused environment.
    *   `#161122` (Deep Indigo/Purple - Main background, Header, Footer)
    *   `#1C152B` (Darker Purple - Section backgrounds)
    *   `#211a32` (Card backgrounds)
*   **Accent Color:** A vibrant purple for calls-to-action, highlights, and key interactive elements.
    *   `#7847ea` (Primary Accent)
    *   `#6c3ddb` (Accent Hover/Darker Shade)
*   **Text Colors:**
    *   `#FFFFFF` (White - Primary headings, key text)
    *   `#E5E7EB` or `text-gray-300` equivalent (Light Gray - Secondary text, navigation links)
    *   `#a393c8` (Muted Purple/Lavender - Descriptive text, footer links, card paragraph text)
*   **Border Colors:** Subtle borders to define elements and sections.
    *   `#2f2447` (Header/Footer borders, often with opacity e.g., `/70`)
    *   `#433465` (Card borders)
    *   `#7847ea/50` (Accent color with opacity for card hover borders)

### 2.2. Typography

*   **Primary Font:** "Plus Jakarta Sans" (preferred for its modern and clean look).
*   **Secondary/Fallback Font:** "Noto Sans", sans-serif.
*   **Headings (H1, H2, H3):**
    *   Weight: Extrabold (H1), Bold (H2, H3).
    *   Tracking: Tight to Tighter (`tracking-tight`, `tracking-tighter`) for a compact, impactful look.
    *   Color: Primarily white (`#FFFFFF`).
    *   Sizes: Large and responsive (e.g., H1: `text-4xl sm:text-5xl md:text-6xl`).
*   **Body Text / Paragraphs:**
    *   Weight: Normal.
    *   Color: Light gray (`text-gray-300`) for general descriptive text, muted purple (`text-[#a393c8]`) for less prominent details or card text.
    *   Line Height: Relaxed (`leading-relaxed`) for readability.
    *   Sizes: Responsive (e.g., `text-base sm:text-lg md:text-xl`).
*   **Links:**
    *   Navigation: `text-gray-300` with `hover:text-white`.
    *   Footer/Inline: `text-[#a393c8]` with `hover:text-white` or `hover:text-[#7847ea]` for social icons.

### 2.3. Iconography

*   **Style:** Clean, modern line icons or filled SVGs where appropriate.
*   **Color:** Often use the accent color (`#7847ea`) or white, sometimes within a subtly colored circular background (`bg-[#7847ea]/20`).
*   **Usage:** To visually support features, actions, and navigation.

## 3. Layout and Structure

*   **Overall Layout:** Full-width sections with centered content containers (`max-w-xl`, `max-w-3xl`, `max-w-5xl` depending on content density).
*   **Responsiveness:** Mobile-first approach using Tailwind CSS utility classes (`sm:`, `md:`, `lg:`) to ensure adaptability across screen sizes.
*   **Spacing:** Generous use of padding and margins (e.g., `py-16 md:py-24`, `px-6 md:px-10`) to create a breathable and uncluttered interface. Gaps between elements should be consistent (e.g., `gap-4`, `gap-8`, `gap-12`).
*   **Grid System:** Utilize CSS Flexbox and Grid for arranging elements within sections (e.g., feature cards, step-by-step guides).
*   **Sticky Header:** The main navigation header should remain visible on scroll (`sticky top-0`) with a background blur effect (`backdrop-blur-md`) and semi-transparent background (`bg-[#161122]/80`) to maintain context without fully obscuring content.

## 4. Component Design

### 4.1. Header

*   **Elements:** Logo, site name, navigation links, primary call-to-action button ("Get Started").
*   **Mobile:** Hamburger menu icon for navigation links.
*   **Styling:** Border bottom, consistent padding, dark background with blur.

### 4.2. Footer

*   **Elements:** Secondary navigation links (About, Contact, Terms, Privacy), social media icons, copyright notice.
*   **Styling:** Border top, consistent padding, dark background.

### 4.3. Buttons

*   **Primary CTA:**
    *   Shape: `rounded-full`.
    *   Background: Accent color (`bg-[#7847ea]`).
    *   Hover: Darker accent color (`hover:bg-[#6c3ddb]`).
    *   Text: White, semibold, with slight letter spacing (`tracking-[0.015em]`).
    *   Sizing: Consistent height (e.g., `h-10`, `h-12`) and padding (`px-5`, `px-6`).
*   **Secondary/Other Buttons:** (To be defined, but should complement the primary style, perhaps using outlines or less prominent background colors).

### 4.4. Cards

*   **Usage:** For displaying features, benefits, testimonials, or distinct pieces of information.
*   **Styling:**
    *   Shape: `rounded-xl`.
    *   Background: `bg-[#211a32]` (slightly lighter than section background).
    *   Border: `border border-[#433465]`.
    *   Hover: `hover:shadow-2xl`, `hover:border-[#7847ea]/50` (accent color border with opacity).
    *   Content: Typically an icon, a heading (`text-xl font-semibold text-white`), and a descriptive paragraph (`text-sm font-normal text-[#a393c8]`).
    *   Alignment: Often `text-center items-center` when an icon is present.

### 4.5. Forms & Inputs

*   (To be defined based on application needs, but should follow the overall dark theme, clarity, and modern aesthetic. Tailwind Forms plugin is used, so leverage its capabilities and customize as needed).

## 5. Interaction and Animation

*   **Hover Effects:** Subtle transitions on interactive elements like buttons (color change) and cards (shadow, border color).
    *   Use `transition-colors`, `transition-all`, `duration-300` for smooth effects.
*   **Focus States:** Clear visual indication for focused elements, especially in forms.
*   **Animations:** Keep animations purposeful and minimal, enhancing user experience rather than distracting. (e.g., subtle fade-ins for content).

## 6. Tone and Voice

*   **Clarity:** Simple, direct, and easy-to-understand language.
*   **Benefit-Oriented:** Focus on how SpendShare helps the user (e.g., "Share expenses, settle in crypto", "Easiest way to split bills").
*   **Trustworthy & Modern:** Language should inspire confidence and reflect a forward-thinking platform.

## 7. Technology Stack (Frontend - Inferred)

*   **HTML:** Semantic and well-structured.
*   **CSS:** Tailwind CSS for utility-first styling.
*   **JavaScript:** (Framework/library not specified in `landing.html`, but will be applied to the existing Svelte frontend).

This design philosophy will guide the redesign of the `./frontend/` Svelte application to align with the visual and structural patterns of `design/landing.html`.