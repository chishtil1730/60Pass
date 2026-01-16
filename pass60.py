import os
import sys
import time
import threading
import pyperclip
import keyboard
import pyautogui
import google.generativeai as genai
from typing import List, Optional

from win10toast import ToastNotifier

class ClipboardGeminiTool:
    def __init__(self):
        self.clipboard_buffer: List[str] = []
        self.current_response: Optional[str] = None
        self.collecting = False
        self.running = True
        self.last_clipboard_content = ""
        self.clipboard_monitor_thread = None
        self.monitor_clipboard = False

        # New attributes for keyboard input feature
        self.typing_mode = False
        self.typed_input = ""
        self.typing_hook = None
        self._blocked_keys = set()

        # New attributes for typing control
        self.typing_in_progress = False
        self.typing_paused = False
        self.typing_stopped = False
        self.typing_thread = None
        self.current_char_index = 0
        self.typing_speed_multiplier = 1.0  # Speed multiplier (1.0 = normal, 2.0 = double speed)

        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY environment variable not set!")
            print("Please set it with: export GEMINI_API_KEY='your_api_key_here'")
            sys.exit(1)

        genai.configure(api_key=api_key)
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini 2.5 Flash API configured successfully")
        except Exception as e:
            print(f"❌ Error configuring Gemini API: {e}")
            sys.exit(1)
        self.notifier = ToastNotifier()






    def add_to_buffer(self):
        """Add current clipboard content to buffer"""
        try:
            # Add a small delay to ensure clipboard content is fully written
            time.sleep(0.1)
            content = pyperclip.paste()
            if content and content.strip():
                # Avoid duplicates
                if not self.clipboard_buffer or content != self.clipboard_buffer[-1]:
                    self.clipboard_buffer.append(content.strip())
                    print(
                        f"📋 Added item {len(self.clipboard_buffer)}: {content[:50]}{'...' if len(content) > 50 else ''}")
                else:
                    print("⚠️  Item already in buffer, skipping duplicate")
            else:
                print("⚠️  Clipboard is empty or contains only whitespace")
        except Exception as e:
            print(f"❌ Error reading clipboard: {e}")

    def monitor_clipboard_changes(self):
        """Monitor clipboard for changes and auto-add when in collecting mode"""
        while self.running:
            try:
                if self.monitor_clipboard and self.collecting:
                    current_content = pyperclip.paste()

                    # Check if clipboard content has changed
                    if (current_content and
                            current_content.strip() and
                            current_content != self.last_clipboard_content):

                        self.last_clipboard_content = current_content

                        # Auto-add to buffer if collecting
                        if not self.clipboard_buffer or current_content.strip() != self.clipboard_buffer[-1]:
                            self.clipboard_buffer.append(current_content.strip())
                            print(
                                f"🔄 Auto-detected copy! Added item {len(self.clipboard_buffer)}: {current_content[:50]}{'...' if len(current_content) > 50 else ''}")

                time.sleep(0.2)  # Check every 200ms

            except Exception as e:
                # Silently continue if there's a clipboard error
                time.sleep(0.5)

    def start_clipboard_monitoring(self):
        """Start monitoring clipboard changes"""
        if not self.clipboard_monitor_thread or not self.clipboard_monitor_thread.is_alive():
            self.monitor_clipboard = True
            self.last_clipboard_content = pyperclip.paste() if pyperclip.paste() else ""
            self.clipboard_monitor_thread = threading.Thread(target=self.monitor_clipboard_changes, daemon=True)
            self.clipboard_monitor_thread.start()

    def stop_clipboard_monitoring(self):
        """Stop monitoring clipboard changes"""
        self.monitor_clipboard = False

    def send_to_gemini(self) -> Optional[str]:
        """Send collected items to Gemini 2.5 Flash"""
        if not self.clipboard_buffer:
            print("⚠️  No items in buffer to send")
            return None

        # Create prompt with all collected items
        prompt_parts = []
        prompt_parts.append("Please analyze and respond to the following collected items:")
        prompt_parts.append("")

        for i, item in enumerate(self.clipboard_buffer, 1):
            prompt_parts.append(f"--- Item {i} ---")
            prompt_parts.append(item)
            prompt_parts.append("")

        prompt_parts.append("Please provide a helpful response based on these items.")

        prompt = "\n".join(prompt_parts)

        print(f"🤖 Sending {len(self.clipboard_buffer)} items to Gemini 2.5 Flash...")
        print(f"📝 Total prompt length: {len(prompt)} characters")

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            # ✅ Show toast when response is ready
            self.notifier.show_toast(
                "Gemini Assistant",
                "✅ Response ready! Choose output method (Paste or Type).",
                duration=5,
                threaded=True
            )

            print("✅ Response received from Gemini!")
            print(f"📄 Response preview: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            return answer
        except Exception as e:
            print(f"❌ Error communicating with Gemini: {e}")
            return None

    def paste_response(self):
        """Paste response via clipboard (Ctrl+L) - instant paste"""
        if not self.current_response:
            print("⚠️  No response available to paste")
            return

        try:
            print("📋 Pasting response via clipboard...")
            # Save current clipboard content
            original_clipboard = pyperclip.paste()

            # Copy response to clipboard
            pyperclip.copy(self.current_response)
            time.sleep(0.1)

            # Try multiple paste methods
            paste_success = False

            # Method 1: pyautogui hotkey
            try:
                pyautogui.hotkey('ctrl', 'v')
                paste_success = True
                print("✅ Response pasted instantly!")
            except Exception as e:
                print(f"⚠️  pyautogui paste failed: {e}")

            if not paste_success:
                # Method 2: keyboard library
                try:
                    keyboard.send('ctrl+v')
                    paste_success = True
                    print("✅ Response pasted via keyboard!")
                except Exception as e:
                    print(f"⚠️  keyboard paste failed: {e}")

            if not paste_success:
                print("❌ Clipboard paste failed. Response is in clipboard - use Ctrl+V manually")

            # Restore original clipboard after a delay
            def restore_clipboard():
                time.sleep(2)
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass

            threading.Thread(target=restore_clipboard, daemon=True).start()

        except Exception as e:
            print(f"❌ Paste failed: {e}")
            print("📋 Trying to copy to clipboard for manual paste...")
            try:
                pyperclip.copy(self.current_response)
                print("✅ Response copied to clipboard - paste manually with Ctrl+V")
            except Exception as e2:
                print(f"❌ Even clipboard copy failed: {e2}")

    def type_response(self):
        """Type response character by character (Ctrl+Shift+L) - with pause/stop controls"""
        if not self.current_response:
            print("⚠️  No response available to type")
            return

        if self.typing_in_progress:
            print("⚠️  Already typing! Use Ctrl+Shift+P to pause or Ctrl+Shift+Z to stop")
            return

        print("⌨️  Starting to type response...")
        print(f"⚡ Current speed: {self.typing_speed_multiplier}x normal")
        print("📍 Position your cursor and wait 3 seconds...")
        print("⏸️  Press Ctrl+Shift+P to pause/resume")
        print("🛑 Press Ctrl+Shift+Z to stop typing")
        print("⚡ Press Ctrl+Shift+F to double speed")
        print("🐌 Press Shift+S to halve speed")
        print("🔄 Press Shift+R to reset speed to normal")

        # Countdown
        for i in range(3, 0, -1):
            print(f"⏳ Starting in {i}...")
            time.sleep(1)

        # Reset typing state
        self.typing_in_progress = True
        self.typing_paused = False
        self.typing_stopped = False
        self.current_char_index = 0

        # Start typing in a separate thread
        self.typing_thread = threading.Thread(target=self._type_text_thread, daemon=True)
        self.typing_thread.start()

    def _type_text_thread(self):
        """Thread function to handle the actual typing with pause/stop support"""
        try:
            total_chars = len(self.current_response)

            while self.current_char_index < total_chars and not self.typing_stopped:
                # Check if paused
                while self.typing_paused and not self.typing_stopped:
                    time.sleep(0.1)

                if self.typing_stopped:
                    break

                # Type current character
                char = self.current_response[self.current_char_index]
                pyautogui.write(char, interval=0)

                self.current_char_index += 1

                # Show progress every 100 characters
                if self.current_char_index % 100 == 0:
                    progress = (self.current_char_index / total_chars) * 100
                    chars_per_sec = 67 * self.typing_speed_multiplier
                    print(
                        f"📝 Progress: {progress:.1f}% ({self.current_char_index}/{total_chars} chars) - Speed: {chars_per_sec:.0f} chars/sec")

                # Calculate delay based on speed multiplier
                base_delay = 0.015  # ~67 chars per second at 1x speed
                actual_delay = base_delay / self.typing_speed_multiplier
                time.sleep(actual_delay)

            # Typing completed
            self.typing_in_progress = False

            if self.typing_stopped:
                print(f"🛑 Typing stopped at character {self.current_char_index}/{total_chars}")
            else:
                print("✅ Response typed successfully!")

        except Exception as e:
            print(f"❌ Typing failed: {e}")
            self.typing_in_progress = False

    def pause_typing(self):
        """Pause or resume typing"""
        if not self.typing_in_progress:
            print("⚠️  No typing in progress")
            return

        self.typing_paused = not self.typing_paused

        if self.typing_paused:
            progress = (self.current_char_index / len(self.current_response)) * 100 if self.current_response else 0
            print(f"⏸️  Typing PAUSED at {progress:.1f}% ({self.current_char_index} chars)")
            print("📍 Press Ctrl++Shfit+P again to resume")
        else:
            print("▶️  Typing RESUMED")

    def increase_typing_speed(self):
        """Double the typing speed (Shift+F)"""
        if not self.typing_in_progress:
            print("⚠️  No typing in progress - speed will apply to next typing session")

        old_speed = self.typing_speed_multiplier
        self.typing_speed_multiplier = min(self.typing_speed_multiplier * 2.0, 64.0)  # Max 16x speed

        chars_per_sec = 200 * self.typing_speed_multiplier
        print(
            f"⚡ Speed increased: {old_speed:.1f}x → {self.typing_speed_multiplier:.1f}x ({chars_per_sec:.0f} chars/sec)")

        if self.typing_speed_multiplier >= 64:
            print("🚀 Maximum speed reached!")

    def decrease_typing_speed(self):
        """Halve the typing speed (Shift+S)"""
        if not self.typing_in_progress:
            print("⚠️  No typing in progress - speed will apply to next typing session")

        old_speed = self.typing_speed_multiplier
        self.typing_speed_multiplier = max(self.typing_speed_multiplier / 2.0, 0.125)  # Min 1/8x speed

        chars_per_sec = 67 * self.typing_speed_multiplier
        print(
            f"🐌 Speed decreased: {old_speed:.1f}x → {self.typing_speed_multiplier:.1f}x ({chars_per_sec:.0f} chars/sec)")

        if self.typing_speed_multiplier <= 0.125:
            print("🐌 Minimum speed reached!")

    def reset_typing_speed(self):
        """Reset typing speed to normal (Shift+R)"""
        old_speed = self.typing_speed_multiplier
        self.typing_speed_multiplier = 1.0

        print(f"🔄 Speed reset: {old_speed:.1f}x → 1.0x (67 chars/sec)")

    def stop_typing(self):
        """Stop typing completely"""
        if not self.typing_in_progress:
            print("⚠️  No typing in progress")
            return

        self.typing_stopped = True
        self.typing_paused = False

        progress = (self.current_char_index / len(self.current_response)) * 100 if self.current_response else 0
        print(f"🛑 Typing STOPPED at {progress:.1f}% ({self.current_char_index} chars)")

        # Wait for typing thread to finish
        if self.typing_thread and self.typing_thread.is_alive():
            self.typing_thread.join(timeout=1.0)

    def show_status(self):
        """Display current status"""
        print("\n" + "=" * 60)
        print("📊 CURRENT STATUS")
        print("=" * 60)
        print(f"📋 Buffer items: {len(self.clipboard_buffer)}")
        print(f"🤖 Response ready: {'Yes' if self.current_response else 'No'}")
        print(f"🔄 Collecting mode: {'Active' if self.collecting else 'Inactive'}")
        print(f"⌨️  Typing mode: {'Active' if self.typing_mode else 'Inactive'}")
        print(f"📝 Typing in progress: {'Yes' if self.typing_in_progress else 'No'}")

        if self.typing_in_progress:
            progress = (self.current_char_index / len(self.current_response)) * 100 if self.current_response else 0
            chars_per_sec = 67 * self.typing_speed_multiplier
            print(f"📊 Typing progress: {progress:.1f}% ({self.current_char_index} chars)")
            print(f"⚡ Typing speed: {self.typing_speed_multiplier:.1f}x ({chars_per_sec:.0f} chars/sec)")
            print(f"⏸️  Typing paused: {'Yes' if self.typing_paused else 'No'}")
        elif self.current_response:
            chars_per_sec = 67 * self.typing_speed_multiplier
            print(f"⚡ Next typing speed: {self.typing_speed_multiplier:.1f}x ({chars_per_sec:.0f} chars/sec)")

        if self.clipboard_buffer:
            print("\n📝 Buffer contents:")
            for i, item in enumerate(self.clipboard_buffer, 1):
                preview = item[:80] + "..." if len(item) > 80 else item
                print(f"  {i}. {preview}")

        print("\n🎯 AVAILABLE ACTIONS:")
        if not self.collecting:
            print("  🚀 Ctrl+Shift+S - Start collecting clipboard items")
        else:
            print("  📋 AUTO-COPY MODE: Just copy (Ctrl+C) anything and it will be auto-added!")
            print("  📋 Ctrl+Shift+A - Manually add current clipboard to buffer")
            print("  ⌨️  Ctrl+Shift+Q - Start typing input mode")
            if self.typing_mode:
                print("  🛑 Ctrl+Shift+E - Stop typing and add to buffer")
            print("  ✅ Ctrl+Enter - Finish collecting and send to Gemini")

        if self.current_response:
            print("\n📥 OUTPUT OPTIONS:")
            print("  📋 Ctrl+L - Paste response instantly (clipboard)")
            print("  ⌨️  Ctrl+Shift+L - Type response with controls")

            if self.typing_in_progress:
                print("\n🎮 TYPING CONTROLS:")
                print("  ⏸️  Ctrl+Shift+P - Pause/Resume typing")
                print("  🛑 Ctrl+Shift+Z - Stop typing")
                print("  ⚡ Ctrl+Shift+F - Double speed (faster)")
                print("  🐌 Shift+S - Half speed (slower)")
                print("  🔄 Shift+R - Reset to normal speed")

        print("\n🛠️  OTHER CONTROLS:")
        print("  🗑️  Ctrl+Shift+X - Clear buffer")
        print("  ❓ Ctrl+Shift+H - Show this help")
        print("  🚪 Esc - Exit program")
        print("=" * 60)

    def clear_buffer(self):
        """Clear the clipboard buffer"""
        # Stop any ongoing typing
        if self.typing_in_progress:
            self.stop_typing()

        self.clipboard_buffer.clear()
        self.current_response = None
        self.collecting = False
        self.stop_clipboard_monitoring()
        # Also stop typing mode if active
        if self.typing_mode:
            self.stop_typing_mode()
        print("🗑️  Buffer cleared!")
        self.show_status()

    def start_collecting(self):
        """Start clipboard collection mode"""
        self.collecting = True
        self.clipboard_buffer.clear()
        self.current_response = None

        # Start clipboard monitoring
        self.start_clipboard_monitoring()

        print("\n🚀 Started collecting mode with AUTO-COPY detection!")
        print("=" * 60)
        print("✨ SUPER EASY: Just copy anything with Ctrl+C and it's automatically added!")
        print("📋 Copy from websites, documents, anywhere - no extra hotkeys needed!")
        print("⌨️  Or press Ctrl+Shift+Q to type input directly")
        print("✅ Press Ctrl+Enter when done collecting")
        print("=" * 60)
        self.show_status()

    def finish_collecting(self):
        """Finish collecting and send to Gemini"""
        if not self.collecting:
            print("⚠️  Not in collecting mode")
            return

        # Stop typing mode if active
        if self.typing_mode:
            print("🛑 Stopping typing mode first...")
            self.stop_typing_mode()

        self.collecting = False
        self.stop_clipboard_monitoring()
        print("\n✅ Finished collecting items")

        if not self.clipboard_buffer:
            print("⚠️  No items collected")
            return

        # ✅ Show toast before sending
        self.notifier.show_toast(
            "Gemini Assistant",
            "📤 Sending collected items to Gemini...",
            duration=4,
            threaded=True
        )

        # Send to Gemini
        response = self.send_to_gemini()
        if response:
            self.current_response = response
            print("\n🎉 Ready! Choose your output method:")
            print("📋 Ctrl+L - Paste instantly")
            print("⌨️  Ctrl+Shift+L - Type with pause/stop controls")

        self.show_status()

    # TYPING INPUT FEATURE
    def start_typing_mode(self):
        """Start keyboard input mode"""
        if not self.collecting:
            print("⚠️  Please start collecting mode first (Ctrl+Shift+S)")
            return

        if self.typing_mode:
            print("⚠️  Already in typing mode! Press Ctrl+Shift+E to stop.")
            return

        self.typing_mode = True
        self.typed_input = ""
        self._blocked_keys = set()
        print("\n⌨️  TYPING MODE ACTIVATED!")
        print("=" * 50)
        print("✏️  Start typing your input now...")
        print("🛑 Press Ctrl+Shift+E when finished")
        print("📝 Everything you type will be captured")
        print("=" * 50)

        # Set up keyboard hook for capturing typed input
        self._setup_typing_hook()

    def _setup_typing_hook(self):
        """Set up keyboard hook to capture all typed input"""

        def on_key_event(e):
            # If typing mode isn't active, let everything pass through
            if not self.typing_mode:
                return True  # Allow other handlers / apps to receive the event

            # Only process key down events
            if e.event_type == keyboard.KEY_DOWN:
                try:
                    name = e.name
                except Exception:
                    name = None

                if name == 'space':
                    self.typed_input += ' '
                elif name == 'enter':
                    self.typed_input += '\n'
                elif name == 'backspace':
                    if self.typed_input:
                        self.typed_input = self.typed_input[:-1]
                elif name == 'tab':
                    self.typed_input += '\t'
                elif name and len(name) == 1 and name.isalpha():
                    # Handle letters (consider shift for uppercase)
                    if keyboard.is_pressed('shift'):
                        self.typed_input += name.upper()
                    else:
                        self.typed_input += name.lower()
                elif name and name.isdigit():
                    # Handle numbers and their shifted symbols
                    if keyboard.is_pressed('shift'):
                        shift_map = {'1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                                     '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'}
                        self.typed_input += shift_map.get(name, name)
                    else:
                        self.typed_input += name
                elif name in ['-', '=', '[', ']', '\\', ';', "'", ',', '.', '/']:
                    # Handle punctuation
                    if keyboard.is_pressed('shift'):
                        shift_punct = {'-': '_', '=': '+', '[': '{', ']': '}',
                                       '\\': '|', ';': ':', "'": '"', ',': '<',
                                       '.': '>', '/': '?'}
                        self.typed_input += shift_punct.get(name, name)
                    else:
                        self.typed_input += name
                elif name == '`':
                    self.typed_input += '~' if keyboard.is_pressed('shift') else '`'

                # Return False to prevent the key from reaching other applications
                return False

            # For non-key-down events just allow pass through
            return True

        # Add the keyboard hook
        self.typing_hook = keyboard.hook(on_key_event)

    def stop_typing_mode(self):
        """Stop keyboard input mode and add typed content to buffer"""
        if not self.typing_mode:
            print("⚠️  Not currently in typing mode")
            return

        self.typing_mode = False

        # Remove the keyboard hook
        if self.typing_hook:
            keyboard.unhook(self.typing_hook)
            self.typing_hook = None

        # Clear blocked keys set (no longer needed to unblock individual keys)
        self._blocked_keys.clear()

        if self.typed_input.strip():
            self.clipboard_buffer.append(self.typed_input.strip())
            print(f"\n✅ TYPING COMPLETE!")
            print("=" * 50)
            print(f"📝 Added typed input to buffer (item {len(self.clipboard_buffer)}):")
            print("--- Typed Content ---")
            # Show first few lines of typed content
            lines = self.typed_input.strip().split('\n')
            for i, line in enumerate(lines[:5]):  # Show first 5 lines
                print(f"   {line}")
            if len(lines) > 5:
                print(f"   ... ({len(lines) - 5} more lines)")
            print("=" * 50)
        else:
            print("\n⚠️  No input was typed")

        self.typed_input = ""

        # Show updated status
        self.show_status()

    def setup_hotkeys(self):
        """Set up all keyboard hotkeys"""
        keyboard.add_hotkey('ctrl+shift+s', self.start_collecting)
        keyboard.add_hotkey('ctrl+shift+a', self.add_to_buffer)
        keyboard.add_hotkey('ctrl+enter', self.finish_collecting)

        # Output options
        keyboard.add_hotkey('ctrl+l', self.paste_response)  # Instant paste
        keyboard.add_hotkey('ctrl+shift+l', self.type_response)  # Controlled typing

        # Typing controls (only work during typing)
        keyboard.add_hotkey('ctrl+shift+p', self.pause_typing)  # Pause/resume
        keyboard.add_hotkey('ctrl+shift+z', self.stop_typing)  # Stop typing

        # Speed controls (work anytime)
        keyboard.add_hotkey('ctrl+shift+f', self.increase_typing_speed)  # Double speed
        keyboard.add_hotkey('shift+s', self.decrease_typing_speed)  # Half speed
        keyboard.add_hotkey('shift+r', self.reset_typing_speed)  # Reset speed

        keyboard.add_hotkey('ctrl+shift+x', self.clear_buffer)
        keyboard.add_hotkey('ctrl+shift+h', self.show_status)
        keyboard.add_hotkey('esc', self.exit_program)

        # Typing input feature
        keyboard.add_hotkey('ctrl+shift+q', self.start_typing_mode)
        keyboard.add_hotkey('ctrl+shift+e', self.stop_typing_mode)

    def exit_program(self):
        """Exit the program"""
        # Stop any ongoing typing
        if self.typing_in_progress:
            self.stop_typing()

        # Clean up typing mode if active
        if self.typing_mode:
            self.typing_mode = False
            if self.typing_hook:
                keyboard.unhook(self.typing_hook)
            # Unblock all keys we blocked
            for key in self._blocked_keys:
                try:
                    keyboard.unblock_key(key)
                except Exception:
                    pass
            self._blocked_keys.clear()

        # Stop clipboard monitoring
        self.stop_clipboard_monitoring()

        print("\n👋 Exiting Multi-Clipboard Gemini Assistant...")
        self.running = False

    def run(self):
        """Main program loop"""
        print("🚀 Multi-Clipboard Gemini Assistant Started!")
        print("🆕 NEW: Automatic clipboard detection - no extra hotkeys needed!")
        print("⌨️  NEW: Controllable typing with pause/stop functionality!")
        print("=" * 60)

        # Set up hotkeys
        self.setup_hotkeys()

        # Show initial status
        self.show_status()

        print("\n⌨️  Hotkeys are active! Waiting for your commands...")

        # Keep the program running
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Program interrupted by user")
        finally:
            print("🔄 Cleaning up...")
            # Stop any ongoing typing
            if self.typing_in_progress:
                self.typing_stopped = True
            # Clean up typing hook if still active
            if self.typing_hook:
                keyboard.unhook(self.typing_hook)
            # Unblock all keys we blocked
            for key in self._blocked_keys:
                try:
                    keyboard.unblock_key(key)
                except Exception:
                    pass
            keyboard.unhook_all_hotkeys()


def main():
    """Entry point"""
    print("🔧 Initializing Multi-Clipboard Gemini Assistant...")

    # Try to import required packages and give helpful error messages
    try:
        import pyperclip
        import keyboard
        import pyautogui
        import google.generativeai
        print("✅ All required packages found!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Please install missing packages with:")
        print("   pip install pyperclip keyboard pyautogui google-generativeai")
        sys.exit(1)

    # Initialize and run
    tool = ClipboardGeminiTool()
    tool.run()


if __name__ == "__main__":
    main()