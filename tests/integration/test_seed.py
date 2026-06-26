from scripts.seed import SEED_ORGANIZATIONS, SEED_PASSWORD


def test_seed_defines_required_evaluation_users() -> None:
    users = {
        email: (organization["slug"], role)
        for organization in SEED_ORGANIZATIONS
        for email, role in organization["users"]
    }

    assert users == {
        "admin@example.com": ("demo", "admin"),
        "analyst@example.com": ("demo", "analyst"),
        "viewer@example.com": ("demo", "viewer"),
        "other-admin@example.com": ("other", "admin"),
    }
    assert SEED_PASSWORD == "password123"


def test_seed_organizations_are_unique_by_slug() -> None:
    slugs = [organization["slug"] for organization in SEED_ORGANIZATIONS]

    assert len(slugs) == len(set(slugs)) == 2
