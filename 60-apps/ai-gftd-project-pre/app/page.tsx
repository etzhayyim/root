import LandingPage from "@/components/landing-page";
import TemplatesSection from "@/components/templates-section";

export default function Home() {
  return (
    <div className="bg-white text-gray-800">
      <LandingPage />
      <TemplatesSection />
    </div>
  );
}
