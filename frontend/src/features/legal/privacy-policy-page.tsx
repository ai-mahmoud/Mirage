import { LegalLayout, LegalSection } from "@/features/legal/legal-layout";
import { CURRENT_VERSIONS } from "@/features/legal/versions";

export function PrivacyPolicyPage() {
  return (
    <LegalLayout title="Privacy Policy" version={CURRENT_VERSIONS.privacyPolicy}>
      <p>
        This Privacy Policy describes what Mirage ("we", "the platform") collects when your organization
        uses it to run behavioral-intelligence interview sessions, and what we do — and deliberately do
        not do — with that data. It applies to both the organization account holder (the interviewer or
        HR user who signs in) and, for the specific behavioral-metadata section below, the interview
        candidate being observed during a live session.
      </p>

      <LegalSection title="1. What we collect from your account">
        <p>When you create a Mirage account, we store your email address, a bcrypt hash of your password
          (never the password itself), your organization name, and your role. If you subscribe to a paid
          plan, Stripe (our payment processor) holds your billing details — we only store a Stripe
          customer reference, never your card number.</p>
      </LegalSection>

      <LegalSection title="2. What we collect during a behavioral session">
        <p>
          During a live session, the platform collects only interaction <em>metadata</em>: cursor
          position and movement timing, click and scroll timestamps, keystroke <strong>timing</strong> —
          never which keys were pressed — and window focus/visibility changes. This is enforced at the
          data-contract level, not just as a policy: the client-side event schema physically cannot carry
          a field for key identity, clipboard content, screen contents, audio, or video, so none of that
          data ever leaves the candidate's browser, encrypted or otherwise.
        </p>
        <p>
          We never access the device's microphone or camera, never read clipboard contents, and never
          take screenshots or record video of any kind.
        </p>
      </LegalSection>

      <LegalSection title="3. How that metadata is used">
        <p>
          Interaction metadata is analyzed by a rule-based evidence engine to produce a "Trust DNA"
          profile and evidence cards, shown to the interviewer alongside a conservative recommendation
          (e.g. "Manual Review Recommended" — never an automated accusation or hiring decision). A human
          always makes the final call; the system only ever assists.
        </p>
      </LegalSection>

      <LegalSection title="4. Data retention and deletion">
        <p>
          Session data is retained for a limited period (currently 90 days from creation) and then
          automatically and permanently deleted. Any organization owner can also delete an individual
          session, or their entire organization's data, at any time from Settings — both are immediate
          and irreversible. You can also request a full export of everything we hold about your
          organization at any time.
        </p>
      </LegalSection>

      <LegalSection title="5. Who we share data with">
        <p>
          We do not sell or rent your data. Behavioral metadata is processed by our own evidence-synthesis
          service and never sent to a third party. Billing data is shared only with Stripe, solely to
          process payments.
        </p>
      </LegalSection>

      <LegalSection title="6. Changes to this policy">
        <p>
          If we materially change what this policy promises, we'll publish a new version here with an
          updated effective date, and ask account holders to re-accept it.
        </p>
      </LegalSection>

      <LegalSection title="7. Contact">
        {/* Placeholder — .example is IANA-reserved for exactly this, so it
            can never resolve to a real inbox. Swap for a real support
            address before this is shown to a real customer. */}
        <p>
          Questions about this policy or a data request: <a className="text-nile-700 underline" href="mailto:support@mirage-platform.example">support@mirage-platform.example</a>.
        </p>
      </LegalSection>
    </LegalLayout>
  );
}
