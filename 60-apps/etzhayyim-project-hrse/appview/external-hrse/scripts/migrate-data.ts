/**
 * @etzhayyim/cyber-freelance#DataMigration
 * データ移行スクリプト
 *
 * freelancers → jobSeekers
 * proposals → applications
 */

// CHARTER-VIOLATION §substrate (ADR-2605172000) — operational script; migrate to MST PDS write path before Council ratifies ETZHAYYIM_SUBSTRATE_MODE=mst.
import postgres from "postgres";

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
	console.error("DATABASE_URL environment variable is not set");
	process.exit(1);
}

const client = postgres(DATABASE_URL);

async function migrateFreelancersToJobSeekers() {
	console.log("Starting migration: freelancers → jobSeekers");

	try {
		// 1. freelancersテーブルからデータを取得
		const freelancers = await client`
			SELECT
				id, userId, nationalityId, workPermitId,
				availableFrom, desiredUnitPriceMin, desiredUnitPriceMax,
				desiredWorkdaysPerWeek, remotePreference, createdAt, updatedAt
			FROM freelancers
		`;

		console.log(`Found ${freelancers.length} freelancers to migrate`);

		// 2. 各freelancerをjobSeekerに変換
		for (const freelancer of freelancers) {
			// jobSeekerが既に存在するかチェック
			const existing = await client`
				SELECT id FROM jobSeekers WHERE userId = ${freelancer.userId}
			`;

			if (existing.length > 0) {
				console.log(`Job seeker already exists for 'userId': ${freelancer.userId}, skipping...`);
				continue;
			}

			// jobSeekerを作成
			await client`
				INSERT INTO jobSeekers (
					id, userId, employmentType, nationalityId, workPermitId,
					availableFrom, desiredUnitPriceMin, desiredUnitPriceMax,
					desiredWorkdaysPerWeek, remotePreference, createdAt, updatedAt
				)
				VALUES (
					${freelancer.id},
					${freelancer.userId},
					'freelance',
					${freelancer.nationalityId},
					${freelancer.workPermitId},
					${freelancer.availableFrom},
					${freelancer.desiredUnitPriceMin},
					${freelancer.desiredUnitPriceMax},
					${freelancer.desiredWorkdaysPerWeek},
					${freelancer.remotePreference},
					${freelancer.createdAt},
					${freelancer.updatedAt}
				)
			`;

			// 3. リレーションデータを移行
			// certifications
			await client`
				INSERT INTO jobSeekerCertifications (jobSeekerId, certificationId)
				SELECT ${freelancer.id}, certificationId
				FROM freelancerCertifications
				WHERE freelancerId = ${freelancer.id}
				ON CONFLICT DO NOTHING
			`;

			// specializations
			await client`
				INSERT INTO jobSeekerSpecializations (jobSeekerId, specializationId)
				SELECT ${freelancer.id}, specializationId
				FROM freelancerSpecializations
				WHERE freelancerId = ${freelancer.id}
				ON CONFLICT DO NOTHING
			`;

			// languages
			await client`
				INSERT INTO jobSeekerLanguages (jobSeekerId, languageId)
				SELECT ${freelancer.id}, languageId
				FROM freelancerLanguages
				WHERE freelancerId = ${freelancer.id}
				ON CONFLICT DO NOTHING
			`;

			console.log(`Migrated freelancer ${freelancer.id} → jobSeeker ${freelancer.id}`);
		}

		console.log("✅ Migration completed: freelancers → jobSeekers");
	} catch (error) {
		console.error("❌ Error migrating freelancers:", error);
		throw error;
	}
}

async function migrateProposalsToApplications() {
	console.log("Starting migration: proposals → applications");

	try {
		// 1. proposalsテーブルからデータを取得
		const proposals = await client`
			SELECT
				id, jobId, freelancerId, message, status, createdAt, updatedAt
			FROM proposals
		`;

		console.log(`Found ${proposals.length} proposals to migrate`);

		// 2. 各proposalをapplicationに変換
		for (const proposal of proposals) {
			// applicationが既に存在するかチェック
			const existing = await client`
				SELECT id FROM applications WHERE id = ${proposal.id}
			`;

			if (existing.length > 0) {
				console.log(`Application already exists with id: ${proposal.id}, skipping...`);
				continue;
			}

			// freelancerIdからjobSeekerIdを取得
			const jobSeeker = await client`
				SELECT id FROM jobSeekers WHERE id = ${proposal.freelancerId}
			`;

			if (jobSeeker.length === 0) {
				console.log(`Job seeker not found for 'freelancerId': ${proposal.freelancerId}, skipping proposal ${proposal.id}...`);
				continue;
			}

			const jobSeekerId = jobSeeker[0].id;

			// applicationを作成
			await client`
				INSERT INTO applications (
					id, jobId, jobSeekerId, agencyId,
					applicantName, applicantEmail, applicantPhone, applicantAddress,
					message, status, sentiment, isRead, createdAt, updatedAt
				)
				VALUES (
					${proposal.id},
					${proposal.jobId},
					${jobSeekerId},
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					${proposal.message},
					${proposal.status || 'NEW'},
					NULL,
					false,
					${proposal.createdAt},
					${proposal.updatedAt}
				)
			`;

			console.log(`Migrated proposal ${proposal.id} → application ${proposal.id}`);
		}

		console.log("✅ Migration completed: proposals → applications");
	} catch (error) {
		console.error("❌ Error migrating proposals:", error);
		throw error;
	}
}

async function updateContractsWithJobSeekers() {
	console.log("Starting update: contracts → add jobSeekerId");

	try {
		// contractsテーブルでfreelancerIdがあるがjobSeekerIdがないレコードを更新
		const contracts = await client`
			SELECT id, freelancerId, jobSeekerId
			FROM contracts
			WHERE freelancerId IS NOT NULL AND jobSeekerId IS NULL
		`;

		console.log(`Found ${contracts.length} contracts to update`);

		for (const contract of contracts) {
			// freelancerIdからjobSeekerIdを取得
			const jobSeeker = await client`
				SELECT id FROM jobSeekers WHERE id = ${contract.freelancerId}
			`;

			if (jobSeeker.length > 0) {
				await client`
					UPDATE contracts
					SET jobSeekerId = ${jobSeeker[0].id}
					WHERE id = ${contract.id}
				`;

				console.log(`Updated contract ${contract.id} with 'jobSeekerId': ${jobSeeker[0].id}`);
			}
		}

		console.log("✅ Update completed: contracts → jobSeekerId");
	} catch (error) {
		console.error("❌ Error updating contracts:", error);
		throw error;
	}
}

async function main() {
	console.log("🚀 Starting data migration...\n");

	try {
		// 1. freelancers → jobSeekers
		await migrateFreelancersToJobSeekers();
		console.log("");

		// 2. proposals → applications
		await migrateProposalsToApplications();
		console.log("");

		// 3. contracts → jobSeekerId更新
		await updateContractsWithJobSeekers();
		console.log("");

		console.log("✅ All migrations completed successfully!");
	} catch (error) {
		console.error("❌ Migration failed:", error);
		process.exit(1);
	} finally {
		await client.end();
	}
}

main();






