"use client";

import { SKILL_LEVELS, type SkillLevel } from "@/lib/skills";

interface SkillSelectorProps {
	categoryName: string;
	skills: string[];
	selectedSkills: Record<string, SkillLevel>;
	onChange: (skills: Record<string, SkillLevel>) => void;
}

export function SkillSelector({
	categoryName,
	skills,
	selectedSkills,
	onChange,
}: SkillSelectorProps) {
	const handleSkillChange = (skillName: string, level: string) => {
		const updated = { ...selectedSkills };

		if (level === "" || level === "未選択") {
			// Remove skill if unselected
			delete updated[skillName];
		} else {
			// Add or update skill level
			updated[skillName] = level as SkillLevel;
		}

		onChange(updated);
	};

	return (
		<div>
			<h3 className="mb-3 text-lg font-medium text-neutral-900 dark:text-neutral-100">
				{categoryName}
			</h3>
			<div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
				{skills.map((skill) => (
					<div key={skill} className="flex items-center gap-2">
						<label
							htmlFor={`skill-${skill}`}
							className="min-w-0 flex-1 text-sm text-neutral-700 dark:text-neutral-300"
						>
							{skill}
						</label>
						<select
							id={`skill-${skill}`}
							value={selectedSkills[skill] || ""}
							onChange={(e) => handleSkillChange(skill, e.target.value)}
							className="w-24 min-h-[36px] rounded-md border border-neutral-300 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
						>
							<option value="">未選択</option>
							{SKILL_LEVELS.map((level) => (
								<option key={level} value={level}>
									{level}
								</option>
							))}
						</select>
					</div>
				))}
			</div>
		</div>
	);
}
