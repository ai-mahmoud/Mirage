import { LegalLayout, LegalSection } from "@/features/legal/legal-layout";
import { CURRENT_VERSIONS } from "@/features/legal/versions";

export function TermsOfServicePage() {
  return (
    <LegalLayout title="Terms of Service" version={CURRENT_VERSIONS.termsOfService}>
      <p>
        These Terms govern your use of Mirage. By creating an account you agree to them. If you're
        agreeing on behalf of an organization, you're confirming you have authority to bind that
        organization.
      </p>

      <LegalSection title="1. What Mirage is">
        <p>
          Mirage is an explainable behavioral-intelligence platform that assists an interviewer in
          evaluating candidate engagement during a remote interview, using interaction metadata only. It
          produces evidence-backed, conservative recommendations. It never makes an autonomous hiring
          decision — a qualified human always reviews the evidence and decides.
        </p>
      </LegalSection>

      <LegalSection title="2. Your responsibilities">
        <p>You (the account holder) agree to:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Inform interview candidates that behavioral interaction metadata is collected during the session before it starts, and comply with any applicable local disclosure/consent laws for your jurisdiction.</li>
          <li>Never use Mirage's output as the sole basis for a hiring decision.</li>
          <li>Not attempt to identify a candidate from behavioral metadata beyond what you already know from the interview itself.</li>
          <li>Keep your account credentials confidential and not share a login across multiple unrelated users.</li>
        </ul>
      </LegalSection>

      <LegalSection title="3. Plans and billing">
        <p>
          The Free plan is limited to a fixed number of sessions per calendar month. The Pro plan is
          billed on a recurring subscription via Stripe and can be cancelled at any time from Settings;
          cancellation takes effect at the end of the current billing period.
        </p>
      </LegalSection>

      <LegalSection title="4. Data ownership and deletion">
        <p>
          You own the data your organization generates. You can export or permanently delete it at any
          time (see the Privacy Policy). We may also automatically delete session data after a retention
          period, described in the Privacy Policy.
        </p>
      </LegalSection>

      <LegalSection title="5. No warranty">
        <p>
          Mirage is provided "as is," under active development, and its recommendations are advisory
          only. We make no guarantee of uptime, accuracy, or fitness for any particular hiring or legal
          purpose. You remain solely responsible for hiring decisions made using the platform.
        </p>
      </LegalSection>

      <LegalSection title="6. Termination">
        <p>
          You may stop using Mirage and delete your organization's data at any time. We may suspend or
          terminate an account that violates these Terms, particularly Section 2.
        </p>
      </LegalSection>

      <LegalSection title="7. Changes to these Terms">
        <p>
          If we materially change these Terms, we'll publish a new version here with an updated effective
          date and ask account holders to re-accept it.
        </p>
      </LegalSection>

      <LegalSection title="8. Contact">
        {/* Placeholder — see privacy-policy-page.tsx's identical note. */}
        <p>
          Questions about these Terms: <a className="text-nile-700 underline" href="mailto:support@mirage-platform.example">support@mirage-platform.example</a>.
        </p>
      </LegalSection>
    </LegalLayout>
  );
}
